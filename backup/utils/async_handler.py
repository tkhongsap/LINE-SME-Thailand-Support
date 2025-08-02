"""
Async handler utilities for LINE webhook processing with proper Flask context management
"""
import logging
import asyncio
from functools import wraps
from flask import current_app
from app import app
from utils.flask_context import with_app_context
from utils.database import with_database_retry

logger = logging.getLogger(__name__)

@with_app_context
@with_database_retry()
def send_error_message_async(user_id, reply_token, language='th', user_context=None):
    """
    Send error message asynchronously with proper context handling.
    This function ensures Flask app context is available for database operations.
    """
    try:
        # Import here to avoid circular imports
        from services.line_service import line_service
        from prompts.sme_prompts import SMEPrompts
        
        # Get error messages with proper language fallback
        error_messages = SMEPrompts.get_error_messages()
        if language not in error_messages:
            language = 'th'  # Fallback to Thai
            
        error_message = error_messages[language].get('processing_error', 
                                                   'ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง')
        
        # Send the message
        line_service.send_text_message(reply_token, error_message)
        logger.info(f"Sent error message to user {user_id} in language {language}")
        
    except Exception as e:
        logger.error(f"Failed to send async error message to {user_id}: {e}")

@with_app_context  
def process_message_with_context(user_id, user_message, reply_token, user_context=None, language='th'):
    """
    Process message with proper Flask application context and database retry logic.
    """
    try:
        # Import services here to avoid circular imports
        from services.openai_service import OpenAIService
        from services.conversation_manager import ConversationManager
        from services.line_service import line_service
        
        # Initialize services
        openai_service = OpenAIService()
        conversation_manager = ConversationManager()
        
        # Process the message with database retry logic
        response = openai_service.process_message(
            user_message=user_message,
            user_context=user_context or {},
            language=language
        )
        
        # Save conversation with retry logic
        conversation_manager.save_conversation(
            user_id=user_id,
            user_name=user_context.get('display_name', 'Unknown') if user_context else 'Unknown',
            message_type='text',
            user_message=user_message,
            bot_response=response,
            language=language
        )
        
        # Send response
        line_service.send_text_message(reply_token, response)
        logger.info(f"Successfully processed message for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {e}")
        # Send error message as fallback
        send_error_message_async(user_id, reply_token, language, user_context)

@with_app_context
def process_file_with_context(user_id, file_content, filename, reply_token, user_context=None, language='th'):
    """
    Process file with proper Flask application context and database retry logic.
    """
    try:
        # Import services here to avoid circular imports
        from services.file_processor import streaming_processor
        from services.conversation_manager import ConversationManager
        from services.line_service import line_service
        
        # Process the file
        response = streaming_processor.process_file(
            file_content, 
            filename, 
            language=language,
            user_context=user_context or {}
        )
        
        # Save conversation
        conversation_manager = ConversationManager()
        conversation_manager.save_conversation(
            user_id=user_id,
            user_name=user_context.get('display_name', 'Unknown') if user_context else 'Unknown',
            message_type='file',
            user_message=f"File: {filename}",
            bot_response=response,
            file_name=filename,
            file_type=filename.split('.')[-1].lower() if '.' in filename else 'unknown',
            language=language
        )
        
        # Send response
        line_service.send_text_message(reply_token, response)
        logger.info(f"Successfully processed file {filename} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing file {filename} for user {user_id}: {e}")
        # Send error message as fallback
        send_error_message_async(user_id, reply_token, language, user_context)

def ensure_async_context_safety(func):
    """
    Decorator to ensure async handlers have proper Flask context and error handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Async handler {func.__name__} failed: {e}")
            # Don't re-raise to prevent task queue from failing
            return None
    
    return wrapper