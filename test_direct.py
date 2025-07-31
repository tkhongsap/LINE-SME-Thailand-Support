#!/usr/bin/env python3
import sys
sys.path.append('/home/runner/workspace')

from app import app
from services.conversation_manager import ConversationManager
from services.openai_service import OpenAIService
from services.line_service_optimized import OptimizedLineService
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize services
conversation_manager = ConversationManager()
openai_service = OpenAIService()
line_service = OptimizedLineService()

# Test with app context
with app.app_context():
    # Test user info
    user_id = "U0aa9b562d6edb7c42aac9668f2215349"
    user_message = "สวัสดีครับ"
    
    print("Testing direct message processing...")
    
    # Get conversation history
    history = conversation_manager.get_conversation_history(user_id)
    print(f"Conversation history items: {len(history)}")
    
    # Get user language
    user_language = conversation_manager.get_user_language(user_id)
    print(f"User language: {user_language}")
    
    # Create user context
    user_context = {
        'language': user_language or 'th',
        'user_id': user_id
    }
    
    # Generate response
    print(f"\nGenerating response for: {user_message}")
    try:
        bot_response = openai_service.generate_text_response(
            user_message, 
            history, 
            user_context
        )
        print(f"Bot response: {bot_response}")
        
        # Try to save conversation
        conversation_manager.save_conversation(
            user_id, 
            "Test User", 
            'text', 
            user_message, 
            bot_response, 
            language='th'
        )
        print("Conversation saved successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()