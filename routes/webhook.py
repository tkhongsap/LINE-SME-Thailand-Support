import logging
from datetime import datetime
from flask import Blueprint, request, abort, jsonify
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, FileMessage,
    FollowEvent, UnfollowEvent, PostbackEvent
)

from services.line_service import LineService
from services.openai_service import OpenAIService
from services.file_processor import FileProcessor
from services.conversation_manager import ConversationManager
from models import WebhookEvent
from app import db
from utils.logger import setup_logger, log_user_interaction
from config import Config
from prompts.sme_prompts import SMEPrompts

logger = setup_logger(__name__)

webhook_bp = Blueprint('webhook', __name__)

# Initialize services
line_service = LineService()
openai_service = OpenAIService()
file_processor = FileProcessor()
conversation_manager = ConversationManager()

@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle LINE webhook events"""
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
        # Verify signature
        if not line_service.verify_signature(body, signature):
            abort(400)
        
        # Parse events
        events = request.json.get('events', [])
        
        for event in events:
            process_event(event)
        
        return 'OK'
        
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        abort(500)

def process_event(event_data):
    """Process individual LINE event"""
    start_time = datetime.utcnow()
    
    try:
        event_type = event_data.get('type')
        user_id = event_data.get('source', {}).get('userId')
        source_type = event_data.get('source', {}).get('type')
        source_id = event_data.get('source', {}).get('groupId') or event_data.get('source', {}).get('roomId') or user_id
        
        # Log webhook event
        webhook_event = WebhookEvent(
            event_type=event_type,
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            message_id=event_data.get('message', {}).get('id')
        )
        
        if event_type == 'message':
            handle_message_event(event_data, webhook_event)
        elif event_type == 'follow':
            handle_follow_event(event_data, webhook_event)
        elif event_type == 'unfollow':
            handle_unfollow_event(event_data, webhook_event)
        elif event_type == 'postback':
            handle_postback_event(event_data, webhook_event)
        
        # Calculate processing time
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        webhook_event.processing_time = processing_time
        webhook_event.processed = True
        
        db.session.add(webhook_event)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        if 'webhook_event' in locals():
            webhook_event.error_message = str(e)
            db.session.add(webhook_event)
            db.session.commit()

def handle_message_event(event_data, webhook_event):
    """Handle message events"""
    try:
        message = event_data.get('message', {})
        message_type = message.get('type')
        reply_token = event_data.get('replyToken')
        user_id = event_data.get('source', {}).get('userId')
        
        if not user_id or not reply_token:
            logger.error("Missing user_id or reply_token")
            return
        
        # Get user profile
        user_profile = line_service.get_user_profile(user_id)
        user_name = user_profile.get('display_name', 'Unknown') if user_profile else 'Unknown'
        
        # Get user's preferred language
        user_language = conversation_manager.get_user_language(user_id)
        
        if message_type == 'text':
            handle_text_message(message, reply_token, user_id, user_name, user_language)
        elif message_type == 'image':
            handle_image_message(message, reply_token, user_id, user_name, user_language)
        elif message_type == 'file':
            handle_file_message(message, reply_token, user_id, user_name, user_language)
        
    except Exception as e:
        logger.error(f"Error handling message event: {e}")
        send_error_message(reply_token, user_language if 'user_language' in locals() else 'th')

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
        
        # Generate AI response
        bot_response = openai_service.generate_text_response(
            user_message, conversation_history, detected_language
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
        
        # Analyze image with AI
        bot_response = openai_service.analyze_image(image_content, language=user_language)
        
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
        
        # Process file
        success, error_code, extracted_text = file_processor.process_file(file_content, filename)
        
        if not success:
            error_messages = SMEPrompts.get_error_messages()
            error_message = error_messages.get(user_language, error_messages['th']).get(error_code, 'Processing error')
            line_service.send_text_message(reply_token, error_message)
            return
        
        # Generate AI response based on file content
        bot_response = openai_service.process_file_content(
            extracted_text, filename, language=user_language
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
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'LINE Bot Webhook'
    })
