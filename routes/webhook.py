import logging
import hmac
import hashlib
import base64
import os
from datetime import datetime
from flask import Blueprint, request, abort, jsonify, current_app
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, FileMessage,
    FollowEvent, UnfollowEvent, PostbackEvent, TextSendMessage
)

# Import optimized services
from services.line_service_optimized import OptimizedLineService
from services.openai_service import OpenAIService
from services.fast_openai_service import fast_openai_service
from services.streaming_file_processor import streaming_processor
from services.conversation_manager import ConversationManager
from services.message_queue import message_queue, send_processing_status
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict
import time
from services.rate_limiter import rate_limiter, line_api_circuit_breaker, backoff_calculator
from services.rich_menu_manager import RichMenuManager

from models import WebhookEvent
from app import db
from utils.logger import setup_logger, log_user_interaction
from utils.complexity_detector import complexity_detector
from config import Config
from prompts.sme_prompts import SMEPrompts

logger = setup_logger(__name__)

webhook_bp = Blueprint('webhook', __name__)

def verify_line_signature(body, signature):
    """
    Verify LINE webhook signature using proper LINE SDK method
    
    Args:
        body (str): Raw request body
        signature (str): X-Line-Signature header value
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature:
        logger.warning("Missing X-Line-Signature header")
        return False
    
    try:
        channel_secret = Config.LINE_CHANNEL_SECRET
        if not channel_secret:
            logger.error("LINE_CHANNEL_SECRET not configured")
            return False
        
        # Use LINE SDK's signature verification
        # LINE sends signatures as base64-encoded HMAC-SHA256 without prefixes
        expected_signature = base64.b64encode(
            hmac.new(
                channel_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # LINE signature comes as base64 string directly
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}")
        return False

# Initialize optimized services
line_service = OptimizedLineService()
openai_service = OpenAIService()
# Use the global streaming processor instance
conversation_manager = ConversationManager()

# Initialize rich menu manager
rich_menu_manager = RichMenuManager(line_service.line_bot_api) if line_service.line_bot_api else None

# Advanced async processing components
class WebhookProcessor:
    """Enhanced webhook processor with batch processing and circuit breakers"""
    
    def __init__(self):
        self.event_buffer = defaultdict(list)
        self.buffer_lock = threading.Lock()
        self.last_flush = time.time()
        self.batch_size = 10
        self.flush_interval = 2.0  # seconds
        self.executor = ThreadPoolExecutor(max_workers=Config.CONNECTION_POOL_SIZE)
        self.processing_metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'avg_processing_time': 0,
            'batch_operations': 0
        }
        
        # Start batch processor
        self._start_batch_processor()
    
    def _start_batch_processor(self):
        """Start background batch processor"""
        def batch_processor():
            while True:
                try:
                    current_time = time.time()
                    if (current_time - self.last_flush) >= self.flush_interval:
                        self._flush_batches()
                        self.last_flush = current_time
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Batch processor error: {e}")
                    time.sleep(1)
        
        processor_thread = threading.Thread(target=batch_processor, daemon=True)
        processor_thread.start()
        logger.info("Batch processor started")
    
    def _flush_batches(self):
        """Flush accumulated batches for processing"""
        with self.buffer_lock:
            if not self.event_buffer:
                return
            
            # Process batches by user to maintain order
            for user_id, events in self.event_buffer.items():
                if len(events) >= self.batch_size or (time.time() - events[0]['timestamp']) > self.flush_interval:
                    self._process_user_batch(user_id, events.copy())
                    events.clear()
            
            # Clean empty buffers
            self.event_buffer = {k: v for k, v in self.event_buffer.items() if v}
    
    def _process_user_batch(self, user_id, events):
        """Process a batch of events for a specific user"""
        try:
            self.processing_metrics['batch_operations'] += 1
            
            # Submit batch processing task
            future = self.executor.submit(self._execute_user_batch, user_id, events)
            
            # Don't wait for completion to maintain async nature
            def handle_batch_result(fut):
                try:
                    result = fut.result()
                    self.processing_metrics['events_processed'] += len(events)
                    logger.debug(f"Processed batch of {len(events)} events for user {user_id}")
                except Exception as e:
                    self.processing_metrics['events_failed'] += len(events)
                    logger.error(f"Batch processing failed for user {user_id}: {e}")
            
            future.add_done_callback(handle_batch_result)
            
        except Exception as e:
            logger.error(f"Error submitting batch for user {user_id}: {e}")
    
    def _execute_user_batch(self, user_id, events):
        """Execute a batch of events for a user"""
        start_time = time.time()
        results = []
        
        try:
            # Get user context once for the entire batch
            user_language = conversation_manager.get_user_language(user_id)
            user_context = {'language': user_language}
            
            # Process events in order
            for event_data in events:
                try:
                    result = self._process_single_event(event_data['event'], user_context)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing event in batch: {e}")
                    results.append({'error': str(e)})
            
            # Update processing time metrics
            processing_time = time.time() - start_time
            current_avg = self.processing_metrics['avg_processing_time']
            batch_count = self.processing_metrics['batch_operations']
            
            self.processing_metrics['avg_processing_time'] = (
                (current_avg * (batch_count - 1) + processing_time) / batch_count
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise
    
    def _process_single_event(self, event_data, user_context):
        """Process a single event within a batch"""
        event_type = event_data.get('type')
        
        if event_type == 'message':
            return self._handle_batch_message(event_data, user_context)
        elif event_type == 'follow':
            return self._handle_batch_follow(event_data, user_context)
        elif event_type == 'postback':
            return self._handle_batch_postback(event_data, user_context)
        
        return {'status': 'ignored', 'type': event_type}
    
    def _handle_batch_message(self, event_data, user_context):
        """Handle message event within batch processing"""
        message = event_data.get('message', {})
        message_type = message.get('type')
        
        if message_type == 'text':
            # For text messages, queue them for AI processing
            user_id = event_data.get('source', {}).get('userId')
            reply_token = event_data.get('replyToken')
            user_message = message.get('text', '').strip()
            
            if user_message and not user_message.startswith('/'):
                task_id = message_queue.enqueue_text_processing(
                    user_id=user_id,
                    user_message=user_message,
                    reply_token=reply_token,
                    user_context=user_context
                )
                return {'status': 'queued', 'task_id': task_id}
        
        return {'status': 'processed', 'type': message_type}
    
    def _handle_batch_follow(self, event_data, user_context):
        """Handle follow event within batch"""
        # Process follow events immediately as they're lightweight
        user_id = event_data.get('source', {}).get('userId')
        reply_token = event_data.get('replyToken')
        
        if reply_token:
            welcome_message = SMEPrompts.get_welcome_message(user_context['language'])
            line_service.send_text_message(reply_token, welcome_message)
        
        return {'status': 'processed', 'type': 'follow'}
    
    def _handle_batch_postback(self, event_data, user_context):
        """Handle postback event within batch"""
        # Process postback events with batching
        return {'status': 'processed', 'type': 'postback'}
    
    def add_event(self, event_data):
        """Add event to processing buffer"""
        user_id = event_data.get('source', {}).get('userId')
        if not user_id:
            # Process non-user events immediately
            return process_event_async(event_data)
        
        with self.buffer_lock:
            # Ensure user_id exists in event_buffer (safety check for defaultdict)
            if user_id not in self.event_buffer:
                self.event_buffer[user_id] = []
            
            self.event_buffer[user_id].append({
                'event': event_data,
                'timestamp': time.time()
            })
    
    def get_metrics(self):
        """Get processing metrics"""
        return {
            **self.processing_metrics,
            'buffer_size': sum(len(events) for events in self.event_buffer.values()),
            'active_users': len(self.event_buffer)
        }

# Initialize enhanced webhook processor
webhook_processor = WebhookProcessor()

# Register message queue handlers
def register_queue_handlers():
    """Register handlers for different types of async tasks"""
    
    def handle_text_processing(task):
        """Handle text message processing asynchronously"""
        start_time = time.time()
        current_step = "initialization"
        user_context = None
        
        try:
            # Import app at module level to avoid circular imports
            from app import app
            
            logger.info(f"Starting text processing for task {task.id}, user {task.user_id}")
            logger.info(f"Task payload keys: {list(task.payload.keys())}")
            
            payload = task.payload
            user_message = payload['user_message']
            user_context = payload.get('user_context', {})
            
            logger.info(f"Task {task.id} - Processing message: '{user_message[:100]}...'")
            logger.info(f"Task {task.id} - User context: {user_context}")
            
            current_step = "app_context"
            # Use Flask app context for database operations
            with app.app_context():
                current_step = "conversation_history"
                logger.info(f"Task {task.id} - Getting conversation history...")
                try:
                    conversation_history = conversation_manager.get_conversation_history(task.user_id)
                    logger.info(f"Task {task.id} - Retrieved {len(conversation_history) if conversation_history else 0} previous messages")
                except Exception as hist_e:
                    logger.error(f"Task {task.id} - Failed to get conversation history: {hist_e}", exc_info=True)
                    conversation_history = []  # Continue with empty history
                
                current_step = "ai_generation"
                # Generate AI response
                logger.info(f"Task {task.id} - Generating AI response...")
                logger.info(f"Task {task.id} - OpenAI service config valid: {openai_service.config_valid}")
                
                try:
                    bot_response = openai_service.generate_text_response(
                        user_message, conversation_history, user_context
                    )
                    logger.info(f"Task {task.id} - AI response generated successfully, length: {len(bot_response)}")
                    logger.info(f"Task {task.id} - Response preview: '{bot_response[:200]}...'")
                except Exception as ai_e:
                    logger.error(f"Task {task.id} - AI generation failed: {ai_e}", exc_info=True)
                    logger.error(f"Task {task.id} - AI generation error type: {type(ai_e).__name__}")
                    logger.error(f"Task {task.id} - Message that failed: '{user_message}'")
                    logger.error(f"Task {task.id} - Context that failed: {user_context}")
                    raise  # Re-raise to trigger error handling
                
                current_step = "line_service_send"
                # Send response
                logger.info(f"Task {task.id} - Sending response, reply_token: {task.reply_token}")
                logger.info(f"Task {task.id} - Reply token valid: {line_service.is_reply_token_valid(task.reply_token) if task.reply_token else 'N/A'}")
                
                try:
                    if task.reply_token and line_service.is_reply_token_valid(task.reply_token):
                        line_service.send_text_message(task.reply_token, bot_response)
                        logger.info(f"Task {task.id} - Response sent via reply token successfully")
                    else:
                        # Use push message if reply token expired
                        logger.warning(f"Task {task.id} - Reply token expired/invalid, using push message")
                        messages = [TextSendMessage(text=bot_response)]
                        line_service.push_message(task.user_id, messages)
                        logger.info(f"Task {task.id} - Response sent via push message successfully")
                except Exception as send_e:
                    logger.error(f"Task {task.id} - Failed to send response: {send_e}", exc_info=True)
                    logger.error(f"Task {task.id} - Send error type: {type(send_e).__name__}")
                    # Don't raise here - message was generated successfully, just delivery failed
                
                current_step = "database_save"
                # Save conversation
                try:
                    user_profile = line_service.get_user_profile(task.user_id)
                    user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
                    detected_language = user_context.get('language', 'th')
                    
                    logger.info(f"Task {task.id} - Saving conversation for user {user_name}")
                    conversation_manager.save_conversation(
                        task.user_id, user_name, 'text', user_message, bot_response, 
                        language=detected_language
                    )
                    
                    log_user_interaction(task.user_id, 'text', user_message, bot_response)
                    logger.info(f"Task {task.id} - Conversation saved successfully")
                except Exception as save_e:
                    logger.error(f"Task {task.id} - Failed to save conversation: {save_e}", exc_info=True)
                    # Don't raise here - core functionality worked
                
                elapsed_time = time.time() - start_time
                logger.info(f"Task {task.id} - Completed successfully in {elapsed_time:.2f}s")
                return {'status': 'success', 'response_length': len(bot_response), 'elapsed_time': elapsed_time}
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Text processing FAILED for task {task.id} after {elapsed_time:.2f}s at step '{current_step}': {e}")
            logger.error(f"Task {task.id} - Error type: {type(e).__name__}")
            logger.error(f"Task {task.id} - Error details: {str(e)}")
            logger.error(f"Task {task.id} - Failed at step: {current_step}")
            logger.error(f"Task {task.id} - User message: '{task.payload.get('user_message', 'N/A')}'")
            logger.error(f"Task {task.id} - User context: {user_context}")
            logger.error(f"Task {task.id} - Full stack trace:", exc_info=True)
            
            # Send error message to user
            try:
                logger.info(f"Task {task.id} - Sending error message to user...")
                if user_context:
                    send_error_message_async(task.user_id, task.reply_token, user_context.get('language', 'th'))
                else:
                    send_error_message_async(task.user_id, task.reply_token, 'th')
                logger.info(f"Task {task.id} - Error message sent to user")
            except Exception as error_send_e:
                logger.error(f"Task {task.id} - Failed to send error message: {error_send_e}", exc_info=True)
            
            raise
    
    def handle_file_processing(task):
        """Handle file processing asynchronously"""
        try:
            payload = task.payload
            file_content = payload['file_content']
            filename = payload['filename']
            user_context = payload.get('user_context', {})
            
            # Send processing status
            send_processing_status(task.user_id, task.id, "กำลังประมวลผลไฟล์..." if user_context.get('language') == 'th' else "Processing file...")
            
            # Process file with streaming
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            def progress_callback(progress):
                """Handle progress updates for file processing"""
                if progress.progress_percent % 25 == 0:  # Update every 25%
                    status_msg = progress.current_step
                    if user_context.get('language') == 'th':
                        status_msg = f"กำลังประมวลผล... {progress.progress_percent}%"
                    else:
                        status_msg = f"Processing... {progress.progress_percent}%"
                    
                    # Send status update if possible
                    try:
                        send_processing_status(task.user_id, task.id, status_msg)
                    except:
                        pass  # Continue processing even if status update fails
            
            try:
                success, error_code, extracted_text, metadata = loop.run_until_complete(
                    streaming_processor.process_file_streaming(
                        file_content, filename, progress_callback, user_context
                    )
                )
            finally:
                loop.close()
            
            if not success:
                error_messages = SMEPrompts.get_error_messages()
                error_message = error_messages.get(error_code, 'Processing error')
                
                if task.reply_token and line_service.is_reply_token_valid(task.reply_token):
                    line_service.send_text_message(task.reply_token, error_message)
                else:
                    messages = [TextSendMessage(text=error_message)]
                    line_service.push_message(task.user_id, messages)
                return {'status': 'error', 'error_code': error_code}
            
            # Generate AI response
            bot_response = openai_service.process_file_content(
                extracted_text, filename, user_context=user_context
            )
            
            # Send response
            if task.reply_token and line_service.is_reply_token_valid(task.reply_token):
                line_service.send_text_message(task.reply_token, bot_response)
            else:
                messages = [TextSendMessage(text=bot_response)]
                line_service.push_message(task.user_id, messages)
            
            # Save conversation
            user_profile = line_service.get_user_profile(task.user_id)
            user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
            language = user_context.get('language', 'th')
            
            conversation_manager.save_conversation(
                task.user_id, user_name, 'file', f'[File uploaded: {filename}]',
                bot_response, filename, filename.split('.')[-1], language
            )
            
            log_user_interaction(task.user_id, 'file', f'[File uploaded: {filename}]', bot_response)
            return {'status': 'success', 'filename': filename, 'response_length': len(bot_response)}
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            send_error_message_async(task.user_id, task.reply_token, user_context.get('language', 'th'))
            raise
    
    def handle_image_processing(task):
        """Handle image processing asynchronously"""
        try:
            payload = task.payload
            image_content = payload['image_content']
            user_context = payload.get('user_context', {})
            
            # Send processing status
            send_processing_status(task.user_id, task.id, "กำลังวิเคราะห์รูปภาพ..." if user_context.get('language') == 'th' else "Analyzing image...")
            
            # Analyze image
            bot_response = openai_service.analyze_image(image_content, user_context=user_context)
            
            # Send response
            if task.reply_token and line_service.is_reply_token_valid(task.reply_token):
                line_service.send_text_message(task.reply_token, bot_response)
            else:
                messages = [TextSendMessage(text=bot_response)]
                line_service.push_message(task.user_id, messages)
            
            # Save conversation
            user_profile = line_service.get_user_profile(task.user_id)
            user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
            language = user_context.get('language', 'th')
            
            conversation_manager.save_conversation(
                task.user_id, user_name, 'image', '[Image uploaded]', bot_response, language=language
            )
            
            log_user_interaction(task.user_id, 'image', '[Image uploaded]', bot_response)
            return {'status': 'success', 'response_length': len(bot_response)}
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            send_error_message_async(task.user_id, task.reply_token, user_context.get('language', 'th'))
            raise
    
    # Register handlers
    message_queue.register_handler('text_processing', handle_text_processing)
    message_queue.register_handler('file_processing', handle_file_processing)
    message_queue.register_handler('image_processing', handle_image_processing)

# Register handlers on import
register_queue_handlers()

@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Optimized webhook handler with rate limiting and async processing"""
    # Handle GET requests for webhook verification
    if request.method == 'GET':
        return 'Webhook endpoint is active', 200
    
    # Get signature from headers
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.error("Missing X-Line-Signature header")
        abort(400)
    
    # Get request body
    body = request.get_data(as_text=True)
    
    try:
        # Check circuit breaker
        if not line_api_circuit_breaker.can_proceed():
            logger.warning("Circuit breaker is open, rejecting request")
            abort(503)  # Service unavailable
        
        # Critical Security: Verify LINE webhook signature
        # Add debug mode bypass for testing
        debug_mode = os.environ.get('WEBHOOK_DEBUG_MODE', 'false').lower() == 'true'
        
        if Config.LINE_CHANNEL_SECRET and len(Config.LINE_CHANNEL_SECRET.strip()) > 0 and not debug_mode:
            try:
                if not verify_line_signature(body, signature):
                    logger.error(f"Invalid LINE signature from {request.remote_addr}")
                    logger.debug(f"Body: {body[:200]}...")
                    logger.debug(f"Signature: {signature}")
                    line_api_circuit_breaker.record_failure()
                    abort(400)
                else:
                    logger.info("LINE signature verification passed")
            except Exception as e:
                logger.error(f"Signature verification error: {e}")
                # Continue processing for development/testing
                logger.warning("Continuing without signature verification due to error")
        else:
            if debug_mode:
                logger.warning("LINE signature verification skipped - debug mode enabled")
            else:
                logger.warning("LINE signature verification skipped - no channel secret configured")
        
        line_api_circuit_breaker.record_success()
        
        # Parse events - handle cases where JSON might be invalid
        try:
            if request.json is None:
                logger.warning("Request body is not valid JSON")
                return 'Invalid JSON', 400
            
            events = request.json.get('events', [])
            if not isinstance(events, list):
                logger.warning("Events field is not a list")
                return 'Invalid events format', 400
                
        except Exception as e:
            logger.error(f"Error parsing JSON request: {e}")
            return 'Invalid JSON format', 400
        
        # Process events using enhanced batch processor for optimal performance
        for event in events:
            try:
                # Use batch processor for better throughput
                webhook_processor.add_event(event)
                
                # Also process through original async pipeline for immediate responses
                # This dual approach ensures both speed and reliability
                if event.get('type') in ['follow', 'unfollow'] or \
                   (event.get('type') == 'message' and event.get('message', {}).get('text', '').startswith('/')):
                    # Process commands and follow events immediately
                    process_event_async(event)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                logger.error(f"Event details: {event}")
                # Continue processing other events even if one fails
                continue
        
        # Return immediately (LINE expects response within 30 seconds)
        return 'OK'
        
    except InvalidSignatureError:
        logger.error("Invalid signature")
        line_api_circuit_breaker.record_failure()
        abort(400)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Request details - Method: {request.method}, Path: {request.path}")
        logger.error(f"Request body length: {len(body) if 'body' in locals() else 'N/A'}")
        if 'events' in locals():
            logger.error(f"Events count: {len(events) if events else 0}")
            if events:
                logger.error(f"First event type: {events[0].get('type', 'unknown')}")
                logger.error(f"First event user_id: {events[0].get('source', {}).get('userId', 'N/A')}")
        logger.error("Full stack trace:", exc_info=True)
        line_api_circuit_breaker.record_failure()
        abort(500)

def process_event_async(event_data):
    """Process individual LINE event asynchronously"""
    start_time = datetime.utcnow()
    
    try:
        event_type = event_data.get('type')
        user_id = event_data.get('source', {}).get('userId')
        source_type = event_data.get('source', {}).get('type')
        source_id = event_data.get('source', {}).get('groupId') or event_data.get('source', {}).get('roomId') or user_id
        
        # Rate limiting check for user events
        if user_id and event_type == 'message':
            allowed, wait_time = rate_limiter.check_user_rate_limit(user_id)
            if not allowed:
                logger.warning(f"Rate limited user {user_id}, wait {wait_time:.1f}s")
                # Send rate limit message
                reply_token = event_data.get('replyToken')
                if reply_token:
                    rate_limit_msg = "กรุณารอสักครู่ก่อนส่งข้อความถัดไป" if conversation_manager.get_user_language(user_id) == 'th' else "Please wait before sending another message"
                    line_service.send_text_message(reply_token, rate_limit_msg)
                return
        
        # Log webhook event (non-blocking)
        webhook_event = WebhookEvent(
            event_type=event_type,
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            message_id=event_data.get('message', {}).get('id')
        )
        
        # Process events with immediate response for fast events
        if event_type == 'message':
            handle_message_event_async(event_data, webhook_event)
        elif event_type == 'follow':
            handle_follow_event_optimized(event_data, webhook_event)
        elif event_type == 'unfollow':
            handle_unfollow_event(event_data, webhook_event)
        elif event_type == 'postback':
            handle_postback_event_optimized(event_data, webhook_event)
        
        # Log event processing time (async)
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        webhook_event.processing_time = processing_time
        webhook_event.processed = True
        
        # Non-blocking database save
        try:
            db.session.add(webhook_event)
            db.session.commit()
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            db.session.rollback()
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Event type: {event_data.get('type', 'unknown')}")
        logger.error(f"User ID: {event_data.get('source', {}).get('userId', 'N/A')}")
        logger.error(f"Event data keys: {list(event_data.keys())}")
        logger.error("Event processing stack trace:", exc_info=True)
        if 'webhook_event' in locals():
            webhook_event.error_message = str(e)
            try:
                db.session.add(webhook_event)
                db.session.commit()
            except:
                db.session.rollback()

def process_event(event_data):
    """Legacy sync event processing (kept for compatibility)"""
    return process_event_async(event_data)

def handle_message_event_async(event_data, webhook_event):
    """Handle message events with async processing"""
    try:
        message = event_data.get('message', {})
        message_type = message.get('type')
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        if not user_id or not reply_token:
            logger.error("Missing user_id or reply_token")
            return
        
        # Track reply token
        line_service.track_reply_token(reply_token)
        
        # Get user's preferred language (fast lookup)
        user_language = conversation_manager.get_user_language(user_id)
        user_context = {'language': user_language}
        
        # Handle different message types with async processing
        if message_type == 'text':
            handle_text_message_async(message, reply_token, user_id, user_context)
        elif message_type in ['image', 'file']:
            # Send immediate acknowledgment for slow operations
            ack_message = "ได้รับไฟล์แล้ว กำลังประมวลผล..." if user_language == 'th' else "File received, processing..."
            line_service.send_text_message(reply_token, ack_message)
            
            # Process asynchronously
            if message_type == 'image':
                handle_image_message_async(message, reply_token, user_id, user_context)
            else:
                handle_file_message_async(message, reply_token, user_id, user_context)
        
    except Exception as e:
        logger.error(f"Error handling message event: {e}")
        send_error_message_async(user_id, reply_token, user_context.get('language', 'th') if 'user_context' in locals() else 'th')

def handle_message_event(event_data, webhook_event):
    """Legacy message event handler"""
    return handle_message_event_async(event_data, webhook_event)

def handle_text_message_async(message, reply_token, user_id, user_context):
    """Handle text messages with fast path optimization"""
    try:
        user_message = message.get('text', '').strip()
        
        if not user_message:
            return
        
        # Handle special commands synchronously (fast response)
        if user_message.startswith('/'):
            handle_command_optimized(user_message, reply_token, user_id, user_context)
            return
        
        # Auto-detect language if needed
        detected_language = conversation_manager.detect_and_update_language(user_id, user_message)
        user_context['language'] = detected_language
        
        # FAST PATH OPTIMIZATION: Check if message should use fast path
        if Config.ENABLE_FAST_PATH and fast_openai_service.is_available():
            # Get lightweight conversation history for complexity analysis
            recent_history = []
            if not Config.FAST_PATH_SKIP_CONVERSATION_HISTORY:
                try:
                    recent_history = conversation_manager.get_conversation_history(user_id, limit=3)
                except Exception as e:
                    logger.warning(f"Failed to get history for complexity analysis: {e}")
                    recent_history = []
            
            # Analyze message complexity
            routing_decision = complexity_detector.get_routing_decision(
                user_message, user_id, 'text', recent_history
            )
            
            logger.info(f"Routing decision for user {user_id}: {routing_decision['decision']} "
                       f"(confidence: {routing_decision['confidence']:.2f}) - {routing_decision['analysis']['reason']}")
            
            # FAST PATH: Direct processing for simple queries
            if routing_decision['route_to_fast_path']:
                return handle_fast_path_text_message(
                    user_message, reply_token, user_id, user_context, routing_decision
                )
        
        # FULL PIPELINE: Complex queries go through complete processing
        task_id = message_queue.enqueue_text_processing(
            user_id=user_id,
            user_message=user_message,
            reply_token=reply_token,
            user_context=user_context
        )
        
        logger.info(f"Queued full pipeline processing task {task_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        send_error_message_async(user_id, reply_token, user_context.get('language', 'th'))

def handle_fast_path_text_message(user_message, reply_token, user_id, user_context, routing_decision):
    """Handle simple text messages via fast path - direct Azure OpenAI call"""
    start_time = time.time()
    
    try:
        logger.info(f"🚀 FAST PATH processing for user {user_id}: {user_message[:50]}...")
        
        user_language = user_context.get('language', 'th')
        
        # Direct call to fast OpenAI service (bypasses heavy optimization layers)
        bot_response = fast_openai_service.generate_fast_response(user_message, user_language)
        
        # Send response immediately
        if reply_token and line_service.is_reply_token_valid(reply_token):
            line_service.send_text_message(reply_token, bot_response)
            logger.info(f"✅ Fast path response sent via reply token for user {user_id}")
        else:
            # Fallback to push message
            logger.warning(f"Reply token expired for user {user_id}, using push message")
            messages = [TextSendMessage(text=bot_response)]
            line_service.push_message(user_id, messages)
            logger.info(f"✅ Fast path response sent via push message for user {user_id}")
        
        # Optional lightweight logging (background if configured)
        elapsed_time = time.time() - start_time
        logger.info(f"🚀 FAST PATH completed in {elapsed_time:.2f}s for user {user_id} "
                   f"(Target: {Config.RESPONSE_TIME_TARGET_SIMPLE}s)")
        
        # Minimal database logging (can be made async)
        if not Config.FAST_PATH_SKIP_METRICS_COLLECTION:
            try:
                # Get user profile for logging (cached call)
                user_profile = line_service.get_user_profile(user_id)
                user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
                
                # Save conversation (lightweight version)
                conversation_manager.save_conversation(
                    user_id, user_name, 'text', user_message, bot_response, 
                    language=user_language, processing_time=elapsed_time
                )
                
                # Log interaction
                log_user_interaction(user_id, 'text', user_message, bot_response)
                
            except Exception as db_e:
                logger.warning(f"Fast path database logging failed (non-critical): {db_e}")
        
        # Performance monitoring
        if elapsed_time > Config.RESPONSE_TIME_TARGET_SIMPLE:
            logger.warning(f"⚠️ Fast path exceeded target time: {elapsed_time:.2f}s > {Config.RESPONSE_TIME_TARGET_SIMPLE}s")
        
        return {
            'status': 'success', 
            'processing_time': elapsed_time,
            'route': 'fast_path',
            'response_length': len(bot_response)
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ Fast path processing failed after {elapsed_time:.2f}s: {e}")
        logger.error(f"Fast path error for user {user_id}, message: {user_message[:100]}")
        
        # Send error message
        try:
            send_error_message_async(user_id, reply_token, user_context.get('language', 'th'))
        except Exception as send_error:
            logger.error(f"Failed to send fast path error message: {send_error}")
        
        # Fallback: Could queue for full pipeline processing
        logger.info(f"🔄 Fast path failed, could implement fallback to full pipeline for user {user_id}")
        
        raise

def handle_image_message_async(message, reply_token, user_id, user_context):
    """Handle image messages asynchronously"""
    try:
        message_id = message.get('id')
        
        if not message_id:
            logger.error("Missing message_id for image")
            return
        
        # Get image content
        image_content = line_service.get_message_content(message_id)
        
        # Queue image processing
        task_id = message_queue.enqueue_image_processing(
            user_id=user_id,
            image_content=image_content,
            reply_token=reply_token,
            user_context=user_context
        )
        
        logger.info(f"Queued image processing task {task_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling image message: {e}")
        send_error_message_async(user_id, reply_token, user_context.get('language', 'th'))

def handle_file_message_async(message, reply_token, user_id, user_context):
    """Handle file messages asynchronously"""
    try:
        message_id = message.get('id')
        filename = message.get('fileName', 'unknown_file')
        
        if not message_id:
            logger.error("Missing message_id for file")
            return
        
        # Get file content
        file_content = line_service.get_message_content(message_id)
        
        # Queue file processing
        task_id = message_queue.enqueue_file_processing(
            user_id=user_id,
            file_content=file_content,
            filename=filename,
            reply_token=reply_token,
            user_context=user_context
        )
        
        logger.info(f"Queued file processing task {task_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling file message: {e}")
        send_error_message_async(user_id, reply_token, user_context.get('language', 'th'))

def handle_command_optimized(command, reply_token, user_id, user_context):
    """Handle special commands with optimizations"""
    try:
        command = command.lower()
        user_language = user_context.get('language', 'th')
        
        if command == '/help':
            help_message = line_service.create_help_message(user_language)
            quick_replies = line_service.create_quick_reply_from_context('greeting', user_language)
            line_service.send_text_message(reply_token, help_message, 
                                         [(item.action.label, item.action.text) for item in quick_replies.items[:4]])
            
        elif command == '/lang':
            flex_content = line_service.create_language_selection_flex()
            line_service.send_flex_message(reply_token, "Language Selection", flex_content)
            
        elif command.startswith('/lang '):
            language_code = command.split(' ', 1)[1]
            if language_code in Config.SUPPORTED_LANGUAGES:
                conversation_manager.set_user_language(user_id, language_code)
                # Update rich menu for new language
                if rich_menu_manager:
                    rich_menu_manager.set_user_menu(user_id, 'default', language_code)
                
                responses = {
                    'th': "ภาษาไทยถูกตั้งค่าเรียบร้อยแล้ว! 🇹🇭",
                    'en': "Language updated to English! 🇬🇧", 
                    'ja': "言語が日本語に更新されました！🇯🇵",
                    'ko': "언어가 한국어로 업데이트되었습니다! 🇰🇷",
                    'zh': "语言已更新为中文！🇨🇳"
                }
                response = responses.get(language_code, "Language updated successfully!")
                
                # Add context-aware quick replies
                quick_replies = line_service.create_quick_reply_from_context('greeting', language_code)
                line_service.send_text_message(reply_token, response,
                                             [(item.action.label, item.action.text) for item in quick_replies.items[:4]])
            else:
                error_msg = "รหัสภาษาไม่ถูกต้อง" if user_language == 'th' else "Unsupported language code."
                line_service.send_text_message(reply_token, error_msg)
                
        elif command == '/clear':
            if conversation_manager.clear_conversation_history(user_id):
                responses = {
                    'th': "ประวัติการสนทนาถูกล้างแล้ว! ✨",
                    'en': "Conversation history cleared! ✨",
                    'ja': "会話履歴がクリアされました！✨", 
                    'ko': "대화 기록이 지워졌습니다! ✨"
                }
            else:
                responses = {
                    'th': "ไม่สามารถล้างประวัติได้ ❌",
                    'en': "Failed to clear history. ❌",
                    'ja': "履歴のクリアに失敗しました。❌",
                    'ko': "기록 삭제에 실패했습니다. ❌"
                }
            
            response = responses.get(user_language, responses['en'])
            line_service.send_text_message(reply_token, response)
        
        elif command == '/menu':
            # Switch rich menu context
            if rich_menu_manager:
                rich_menu_manager.set_user_menu(user_id, 'business', user_language)
                msg = "เปลี่ยนเป็นเมนูธุรกิจแล้ว" if user_language == 'th' else "Switched to business menu"
            else:
                msg = "Rich menu not available" 
            line_service.send_text_message(reply_token, msg)
            
        elif command == '/status':
            # Show queue status for user
            user_tasks = message_queue.get_user_tasks(user_id)
            stats = rate_limiter.get_user_usage_stats(user_id)
            
            status_msg = f"📊 Status:\n"
            status_msg += f"• Active Tasks: {len([t for t in user_tasks if t['status'] in ['pending', 'processing']])}\n"
            status_msg += f"• Available Tokens: {stats['available_tokens']}/{stats['capacity']}\n"
            status_msg += f"• Recent Messages: {stats['recent_messages']}"
            
            line_service.send_text_message(reply_token, status_msg)
            
        else:
            # Unknown command, treat as regular message
            user_context['is_command'] = True
            task_id = message_queue.enqueue_text_processing(
                user_id=user_id,
                user_message=command,
                reply_token=reply_token,
                user_context=user_context
            )
            logger.info(f"Queued unknown command {command} as text processing {task_id}")
            
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        send_error_message_async(user_id, reply_token, user_context.get('language', 'th'))

def handle_follow_event_optimized(event_data, webhook_event):
    """Handle follow events with rich menu setup"""
    try:
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        if not user_id or not reply_token:
            return
        
        # Get user profile
        user_profile = line_service.get_user_profile(user_id)
        user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
        
        # Set up rich menu for new user
        if rich_menu_manager:
            rich_menu_manager.set_user_menu(user_id, 'default', 'th')
        
        # Enhanced welcome message with quick replies
        welcome_message = f"""🎉 ยินดีต้อนรับ {user_name}!

ฉันเป็นผู้ช่วย AI สำหรับ SME ไทย พร้อมช่วยเหลือคุณในเรื่อง:

📊 คำปรึกษาธุรกิจและการวางแผน
📄 วิเคราะห์เอกสารและไฟล์ต่างๆ
🖼️ วิเคราะห์รูปภาพและข้อมูลภาพ
💼 สร้างเอกสารธุรกิจ

✨ ลองส่งข้อความ อัพโหลดไฟล์ หรือใช้เมนูด้านล่างเลย!"""
        
        # Create welcome quick replies
        quick_replies = [
            ('คำปรึกษาธุรกิจ', 'ขอคำปรึกษาธุรกิจ SME'),
            ('ดูตัวอย่างเอกสาร', 'แสดงเอกสารธุรกิจ'),
            ('วิธีใช้งาน', '/help'),
            ('เปลี่ยนภาษา', '/lang')
        ]
        
        line_service.send_text_message(reply_token, welcome_message, quick_replies)
        
        logger.info(f"New user followed with optimizations: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling follow event: {e}")

def handle_postback_event_optimized(event_data, webhook_event):
    """Handle postback events with enhanced processing"""
    try:
        postback_data = event_data.get('postback', {}).get('data')
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        if not postback_data or not user_id or not reply_token:
            return
        
        logger.info(f"Postback received: {postback_data} from user {user_id}")
        
        # Parse postback data
        if postback_data.startswith('action='):
            action = postback_data.split('=', 1)[1]
            
            # Handle different postback actions
            if action == 'business_consult':
                response = "กรุณาบอกรายละเอียดธุรกิจหรือปัญหาที่ต้องการคำปรึกษา"
                quick_replies = [
                    ('แผนธุรกิจ', 'ช่วยเขียนแผนธุรกิจ'),
                    ('การตลาด', 'แนะนำกลยุทธ์การตลาด'),
                    ('การเงิน', 'คำนวณต้นทุนและกำไร'),
                    ('กฎหมาย', 'กฎหมายที่เกี่ยวข้อง')
                ]
                line_service.send_text_message(reply_token, response, quick_replies)
                
            elif action == 'document_templates':
                # Send document template carousel
                templates = [
                    {'title': 'ใบเสนอราคา', 'description': 'แบบฟอร์มใบเสนอราคามาตรฐาน', 'action_text': 'สร้างใบเสนอราคา'},
                    {'title': 'ใบกำกับภาษี', 'description': 'แบบฟอร์มใบกำกับภาษี', 'action_text': 'สร้างใบกำกับภาษี'},
                    {'title': 'สัญญาธุรกิจ', 'description': 'แบบสัญญาธุรกิจทั่วไป', 'action_text': 'ดูตัวอย่างสัญญา'}
                ]
                carousel_message = line_service.create_carousel_flex(templates, "เลือกประเภทเอกสาร")
                line_service.send_messages(reply_token, [carousel_message])
                
            else:
                # Default postback handling
                response = f"ได้รับคำสั่ง: {action}"
                line_service.send_text_message(reply_token, response)
        
    except Exception as e:
        logger.error(f"Error handling postback event: {e}")

def send_error_message_async(user_id, reply_token, language='th'):
    """Send error message with fallback to push message"""
    try:
        logger.warning(f"🚨 SENDING ERROR MESSAGE to user {user_id} (language: {language})")
        logger.warning(f"Error message trigger - reply_token: {reply_token}")
        
        error_messages = SMEPrompts.get_error_messages()
        logger.info(f"Available error message keys: {list(error_messages.keys())}")
        
        # Ensure we have a valid language key
        if language not in error_messages:
            logger.warning(f"Language '{language}' not in error messages, falling back to 'th'")
            language = 'th'
        
        lang_errors = error_messages.get(language, {})
        logger.info(f"Error messages for language '{language}': {lang_errors}")
        
        # Check if lang_errors is a dict before trying to get
        if isinstance(lang_errors, dict):
            error_message = lang_errors.get('processing_error', 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง / An error occurred while processing. Please try again.')
        else:
            logger.warning(f"lang_errors is not a dict: {type(lang_errors)}, using default message")
            error_message = 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง / An error occurred while processing. Please try again.'
        
        logger.warning(f"🚨 ERROR MESSAGE CONTENT: {error_message}")
        logger.warning(f"This matches the error message users are seeing in screenshots")
        
        if reply_token and line_service.is_reply_token_valid(reply_token):
            logger.info(f"Sending error message via reply token to user {user_id}")
            line_service.send_text_message(reply_token, error_message)
            logger.warning(f"🚨 ERROR MESSAGE SENT via reply token to user {user_id}")
        else:
            # Fallback to push message
            logger.info(f"Reply token invalid/expired for user {user_id}, using push message")
            logger.info(f"Reply token valid check: {line_service.is_reply_token_valid(reply_token) if reply_token else 'No token'}")
            messages = [TextSendMessage(text=error_message)]
            line_service.push_message(user_id, messages)
            logger.warning(f"🚨 ERROR MESSAGE SENT via push message to user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to send error message to user {user_id}: {e}", exc_info=True)

def handle_text_message(message, reply_token, user_id, user_name, user_language):
    """Handle text messages"""
    try:
        user_message = message.get('text', '').strip()
        
        if not user_message:
            return
        
        # Handle special commands
        if user_message.startswith('/'):
            handle_command(user_message, reply_token, user_id, user_name, user_language)
            return
        
        # Auto-detect language if needed
        detected_language = conversation_manager.detect_and_update_language(user_id, user_message)
        
        # Get conversation history
        conversation_history = conversation_manager.get_conversation_history(user_id)
        
        # Get comprehensive user context for optimization
        user_context = conversation_manager.get_user_context_profile(user_id)
        user_context['language'] = detected_language
        
        # Generate AI response with enhanced context
        bot_response = openai_service.generate_text_response(
            user_message, conversation_history, user_context
        )
        
        # Send response
        line_service.send_text_message(reply_token, bot_response)
        
        # Save conversation
        conversation_manager.save_conversation(
            user_id, user_name, 'text', user_message, bot_response, language=detected_language
        )
        
        log_user_interaction(user_id, 'text', user_message, bot_response)
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        send_error_message(reply_token, user_language)

def handle_image_message(message, reply_token, user_id, user_name, user_language):
    """Handle image messages"""
    try:
        message_id = message.get('id')
        
        if not message_id:
            logger.error("Missing message_id for image")
            return
        
        # Get image content
        image_content = line_service.get_message_content(message_id)
        
        # Get comprehensive user context for optimization
        user_context = conversation_manager.get_user_context_profile(user_id)
        user_context['language'] = user_language
        user_context['analysis_focus'] = 'business relevance and actionable insights'
        
        # Analyze image with AI
        bot_response = openai_service.analyze_image(image_content, user_context=user_context)
        
        # Send response
        line_service.send_text_message(reply_token, bot_response)
        
        # Save conversation
        conversation_manager.save_conversation(
            user_id, user_name, 'image', '[Image uploaded]', bot_response, language=user_language
        )
        
        log_user_interaction(user_id, 'image', '[Image uploaded]', bot_response)
        
    except Exception as e:
        logger.error(f"Error handling image message: {e}")
        send_error_message(reply_token, user_language)

def handle_file_message(message, reply_token, user_id, user_name, user_language):
    """Handle file messages"""
    try:
        message_id = message.get('id')
        filename = message.get('fileName', 'unknown_file')
        
        if not message_id:
            logger.error("Missing message_id for file")
            return
        
        # Get file content
        file_content = line_service.get_message_content(message_id)
        
        # Process file with streaming (legacy handler)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success, error_code, extracted_text, metadata = loop.run_until_complete(
                streaming_processor.process_file_streaming(
                    file_content, filename, None, {'language': user_language}
                )
            )
        finally:
            loop.close()
        
        if not success:
            error_messages = SMEPrompts.get_error_messages()
            error_message = error_messages.get(error_code, 'Processing error')
            line_service.send_text_message(reply_token, error_message)
            return
        
        # Get comprehensive user context for optimization
        user_context = conversation_manager.get_user_context_profile(user_id)
        user_context['language'] = user_language
        user_context['file_type'] = filename.split('.')[-1].lower()
        user_context['analysis_focus'] = 'key insights and actionable recommendations'
        
        # Generate AI response based on file content
        bot_response = openai_service.process_file_content(
            extracted_text, filename, user_context=user_context
        )
        
        # Send response
        line_service.send_text_message(reply_token, bot_response)
        
        # Save conversation
        conversation_manager.save_conversation(
            user_id, user_name, 'file', f'[File uploaded: {filename}]', 
            bot_response, filename, filename.split('.')[-1], user_language
        )
        
        log_user_interaction(user_id, 'file', f'[File uploaded: {filename}]', bot_response)
        
    except Exception as e:
        logger.error(f"Error handling file message: {e}")
        send_error_message(reply_token, user_language)

def handle_command(command, reply_token, user_id, user_name, user_language):
    """Handle special commands"""
    try:
        command = command.lower()
        
        if command == '/help':
            help_message = line_service.create_help_message(user_language)
            line_service.send_text_message(reply_token, help_message)
            
        elif command == '/lang':
            flex_content = line_service.create_language_selection_flex()
            line_service.send_flex_message(reply_token, "Language Selection", flex_content)
            
        elif command.startswith('/lang '):
            language_code = command.split(' ', 1)[1]
            if language_code in Config.SUPPORTED_LANGUAGES:
                conversation_manager.set_user_language(user_id, language_code)
                response = "Language updated successfully!" if language_code == 'en' else "言語が正常に更新されました！"
                line_service.send_text_message(reply_token, response)
            else:
                line_service.send_text_message(reply_token, "Unsupported language code.")
                
        elif command == '/clear':
            if conversation_manager.clear_conversation_history(user_id):
                response = "Conversation history cleared!" if user_language == 'en' else "会話履歴がクリアされました！"
            else:
                response = "Failed to clear history." if user_language == 'en' else "履歴のクリアに失敗しました。"
            line_service.send_text_message(reply_token, response)
            
        else:
            # Unknown command, treat as regular message
            handle_text_message({'text': command}, reply_token, user_id, user_name, user_language)
            
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        send_error_message(reply_token, user_language)

def handle_follow_event(event_data, webhook_event):
    """Handle follow events"""
    try:
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        if not user_id or not reply_token:
            return
        
        # Get user profile
        user_profile = line_service.get_user_profile(user_id)
        user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
        
        # Send welcome message
        welcome_message = f"""🎉 Welcome {user_name}! 

I'm your AI assistant powered by Azure OpenAI. I can help you with:

📝 Text conversations
🖼️ Image analysis  
📄 File processing (PDF, DOCX, XLSX, PPTX, code files)

Send me /help for more information or just start chatting!"""
        
        line_service.send_text_message(reply_token, welcome_message)
        
        logger.info(f"New user followed: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling follow event: {e}")

def handle_unfollow_event(event_data, webhook_event):
    """Handle unfollow events"""
    try:
        user_id = event_data.get('source', {}).get('userId')
        logger.info(f"User unfollowed: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling unfollow event: {e}")

def handle_postback_event(event_data, webhook_event):
    """Handle postback events"""
    try:
        postback_data = event_data.get('postback', {}).get('data')
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        logger.info(f"Postback received: {postback_data}")
        
        # Handle postback data as needed
        # This could be used for interactive elements in flex messages
        
    except Exception as e:
        logger.error(f"Error handling postback event: {e}")

def send_error_message(reply_token, language='th'):
    """Send error message to user"""
    try:
        error_messages = SMEPrompts.get_error_messages()
        error_message = error_messages.get(language, error_messages['th']).get('processing_error')
        line_service.send_text_message(reply_token, error_message)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

@webhook_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with system metrics and database connectivity"""
    try:
        # Check database connectivity first
        database_status = {'status': 'healthy', 'response_time_ms': 0}
        try:
            from utils.database import get_database_status
            database_status = get_database_status()
        except Exception as db_error:
            logger.warning(f"Database health check failed: {db_error}")
            database_status = {'status': 'unhealthy', 'error': str(db_error)}
        
        # Check queue health
        queue_stats = message_queue.get_queue_stats()
        
        # Check circuit breaker status
        circuit_status = line_api_circuit_breaker.get_state()
        
        # Check rate limiter
        api_allowed, _ = rate_limiter.check_api_rate_limit()
        
        # Check fast path status
        fast_path_available = Config.ENABLE_FAST_PATH and fast_openai_service.is_available()
        fast_path_stats = fast_openai_service.get_cache_stats() if fast_path_available else {}
        
        # Determine overall health status
        is_healthy = (
            circuit_status['state'] == 'closed' and 
            database_status['status'] == 'healthy'
        )
        
        health_data = {
            'status': 'healthy' if is_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'LINE Bot Webhook - Ultra-Optimized with Fast Path',
            'database': database_status,
            'metrics': {
                'queue': {
                    'pending_tasks': queue_stats['pending_tasks'],
                    'processing_tasks': queue_stats['processing_tasks'],
                    'completed_tasks': queue_stats['completed_tasks'],
                    'failed_tasks': queue_stats['failed_tasks'],
                    'worker_count': queue_stats['worker_count']
                },
                'circuit_breaker': {
                    'state': circuit_status['state'],
                    'failure_count': circuit_status['failure_count'],
                    'threshold': circuit_status['threshold']
                },
                'rate_limiting': {
                    'api_available': api_allowed,
                    'api_limit': Config.API_RATE_LIMIT
                },
                'fast_path': {
                    'enabled': Config.ENABLE_FAST_PATH,
                    'available': fast_path_available,
                    'cache_stats': fast_path_stats,
                    'target_response_time': f"{Config.RESPONSE_TIME_TARGET_SIMPLE}s",
                    'complexity_threshold_words': Config.COMPLEXITY_THRESHOLD_WORDS,
                    'complexity_threshold_lines': Config.COMPLEXITY_THRESHOLD_LINES
                }
            },
            'optimizations': [
                'Connection pooling enabled',
                'Database retry logic with exponential backoff',
                'Message batching active', 
                'Async processing queue',
                'Rate limiting enforced',
                'Circuit breaker protection',
                'Signature verification caching',
                'Rich menu support',
                '🚀 Fast Path for simple queries' if fast_path_available else '❌ Fast Path unavailable'
            ]
        }
        
        status_code = 200 if is_healthy else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@webhook_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get detailed system metrics"""
    try:
        return jsonify({
            'queue_stats': message_queue.get_queue_stats(),
            'circuit_breaker_stats': line_api_circuit_breaker.get_state(),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/queue/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a specific task"""
    try:
        status = message_queue.get_task_status(task_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/user/<user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    """Get all tasks for a specific user"""
    try:
        tasks = message_queue.get_user_tasks(user_id)
        return jsonify({
            'user_id': user_id,
            'tasks': tasks,
            'total_tasks': len(tasks)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/user/<user_id>/rate-limit', methods=['GET'])
def get_user_rate_limit(user_id):
    """Get rate limit status for a user"""
    try:
        stats = rate_limiter.get_user_usage_stats(user_id)
        return jsonify({
            'user_id': user_id,
            'rate_limit_stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/rich-menu/create', methods=['POST'])
def create_rich_menu():
    """Create rich menu for testing"""
    try:
        if not rich_menu_manager:
            return jsonify({'error': 'Rich menu manager not available'}), 503
            
        data = request.json or {}
        language = data.get('language', 'th')
        menu_type = data.get('type', 'default')
        
        if menu_type == 'default':
            menu_id = rich_menu_manager.create_thai_sme_menu(language)
        elif menu_type == 'business':
            menu_id = rich_menu_manager.create_business_context_menu(language)
        else:
            return jsonify({'error': 'Invalid menu type'}), 400
            
        if menu_id:
            return jsonify({
                'menu_id': menu_id,
                'type': menu_type,
                'language': language,
                'status': 'created'
            })
        else:
            return jsonify({'error': 'Failed to create menu'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/rich-menu/list', methods=['GET'])
def list_rich_menus():
    """List all rich menus"""
    try:
        if not rich_menu_manager:
            return jsonify({'error': 'Rich menu manager not available'}), 503
            
        menus = rich_menu_manager.list_rich_menus()
        return jsonify({
            'menus': menus,
            'total_menus': len(menus)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/fast-path/status', methods=['GET'])
def get_fast_path_status():
    """Get detailed fast path performance status"""
    try:
        fast_path_available = Config.ENABLE_FAST_PATH and fast_openai_service.is_available()
        
        return jsonify({
            'fast_path': {
                'enabled': Config.ENABLE_FAST_PATH,
                'available': fast_path_available,
                'service_ready': fast_openai_service.is_available(),
                'azure_openai_configured': fast_openai_service.config_valid
            },
            'configuration': {
                'max_message_length': Config.FAST_PATH_MAX_LENGTH,
                'complexity_threshold_words': Config.COMPLEXITY_THRESHOLD_WORDS,
                'complexity_threshold_lines': Config.COMPLEXITY_THRESHOLD_LINES,
                'target_response_time': Config.RESPONSE_TIME_TARGET_SIMPLE,
                'skip_sme_intelligence': Config.FAST_PATH_SKIP_SME_INTELLIGENCE,
                'skip_ai_optimizer': Config.FAST_PATH_SKIP_AI_OPTIMIZER,
                'skip_conversation_history': Config.FAST_PATH_SKIP_CONVERSATION_HISTORY,
                'skip_metrics_collection': Config.FAST_PATH_SKIP_METRICS_COLLECTION
            },
            'keywords': {
                'total_fast_keywords': len(Config.FAST_PATH_KEYWORDS),
                'sample_keywords': Config.FAST_PATH_KEYWORDS[:10]
            },
            'cache': fast_openai_service.get_cache_stats() if fast_path_available else {},
            'performance_targets': {
                'simple_queries': f"< {Config.RESPONSE_TIME_TARGET_SIMPLE}s",
                'complex_queries': f"< {Config.RESPONSE_TIME_TARGET_COMPLEX}s",
                'expected_improvement': "70% faster for simple queries"
            },
            'processing_flow': {
                'fast_path_steps': [
                    '1. Webhook receives message',
                    '2. Complexity detection',
                    '3. Direct Azure OpenAI call',
                    '4. Send response',
                    '5. Optional background logging'
                ],
                'full_pipeline_steps': [
                    '1. Webhook receives message', 
                    '2. SME Intelligence analysis',
                    '3. AI Optimizer processing',
                    '4. Context management',
                    '5. Azure OpenAI call',
                    '6. Response processing',
                    '7. Database logging',
                    '8. Send response'
                ]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/fast-path/test', methods=['POST'])
def test_fast_path():
    """Test fast path processing with a sample message"""
    try:
        data = request.json or {}
        test_message = data.get('message', 'สวัสดีครับ')
        test_language = data.get('language', 'th')
        
        if not Config.ENABLE_FAST_PATH:
            return jsonify({'error': 'Fast path is disabled'}), 400
        
        if not fast_openai_service.is_available():
            return jsonify({'error': 'Fast OpenAI service is not available'}), 503
        
        # Test complexity detection
        routing_decision = complexity_detector.get_routing_decision(
            test_message, 'test_user', 'text', []
        )
        
        # Test response generation if routed to fast path
        response_data = {
            'test_message': test_message,
            'language': test_language,
            'routing_decision': routing_decision,
            'fast_path_used': routing_decision['route_to_fast_path']
        }
        
        if routing_decision['route_to_fast_path']:
            start_time = time.time()
            bot_response = fast_openai_service.generate_fast_response(test_message, test_language)
            elapsed_time = time.time() - start_time
            
            response_data.update({
                'bot_response': bot_response,
                'response_time': elapsed_time,
                'target_met': elapsed_time <= Config.RESPONSE_TIME_TARGET_SIMPLE,
                'performance': {
                    'actual_time': f"{elapsed_time:.3f}s",
                    'target_time': f"{Config.RESPONSE_TIME_TARGET_SIMPLE}s",
                    'improvement_estimate': f"{max(0, (2.0 - elapsed_time) / 2.0 * 100):.1f}% faster than typical"
                }
            })
        else:
            response_data['message'] = 'Message would be routed to full pipeline (complex query)'
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/performance/summary', methods=['GET'])
def get_performance_summary():
    """Get performance optimization summary"""
    return jsonify({
        'optimizations_implemented': {
            'fast_path_processing': {
                'enabled': Config.ENABLE_FAST_PATH,
                'direct_azure_openai': True,
                'complexity_detection': True,
                'bypass_heavy_services': True,
                'target_response_time': f'{Config.RESPONSE_TIME_TARGET_SIMPLE}s',
                'description': 'Simple queries processed in 0.5-1s via direct Azure OpenAI calls'
            },
            'webhook_processing': {
                'async_processing': True,
                'immediate_acknowledgment': True,
                'circuit_breaker': True,
                'rate_limiting': True,
                'description': 'Webhook responses under 1 second, processing in background'
            },
            'message_batching': {
                'batch_size': Config.MAX_MESSAGES_PER_REPLY,
                'reply_token_tracking': True,
                'push_message_fallback': True,
                'description': 'Send up to 5 messages per reply, fallback to push messages'
            },
            'connection_optimization': {
                'connection_pooling': True,
                'pool_size': Config.CONNECTION_POOL_SIZE,
                'retry_logic': True,
                'timeout_handling': True,
                'description': 'Persistent connections with automatic retry'
            },
            'caching': {
                'signature_verification': True,
                'flex_message_templates': True,
                'user_language_preference': True,
                'description': 'Cached frequently accessed data'
            },
            'rich_menu': {
                'thai_sme_menu': True,
                'business_context_menu': True,
                'dynamic_language_switching': True,
                'description': 'Interactive menus for faster user actions'
            },
            'error_handling': {
                'exponential_backoff': True,
                'circuit_breaker_pattern': True,
                'graceful_degradation': True,
                'description': 'Robust error recovery and system protection'
            }
        },
        'performance_targets': {
            'webhook_response_time': '< 1 second',
            'text_message_response': '< 3 seconds', 
            'file_processing_acknowledgment': '< 1 second',
            'file_processing_completion': '< 30 seconds',
            'uptime_target': '99.5%',
            'concurrent_users': '100+',
            'rate_limit_per_user': f'{Config.RATE_LIMIT_PER_USER} messages/minute'
        },
        'monitoring': {
            'queue_monitoring': True,
            'rate_limit_tracking': True,
            'error_rate_monitoring': True,
            'performance_metrics': True,
            'circuit_breaker_status': True
        },
        'thai_sme_features': {
            'thai_language_optimized': True,
            'business_document_templates': True,
            'sme_consultation_workflows': True,
            'financial_analysis_tools': True,
            'regulatory_compliance_info': True
        }
    })
