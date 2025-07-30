import logging
from datetime import datetime, timedelta
from sqlalchemy import desc
from app import db
from models import Conversation
from utils.logger import setup_logger
from utils.validators import detect_language
from config import Config

logger = setup_logger(__name__)

class ConversationManager:
    def __init__(self):
        self.max_history = Config.MAX_CONVERSATION_HISTORY
    
    def save_conversation(self, user_id, user_name, message_type, user_message, 
                         bot_response, file_name=None, file_type=None, language='en'):
        """Save conversation to database"""
        try:
            conversation = Conversation(
                user_id=user_id,
                user_name=user_name,
                message_type=message_type,
                user_message=user_message,
                bot_response=bot_response,
                file_name=file_name,
                file_type=file_type,
                language=language
            )
            
            db.session.add(conversation)
            db.session.commit()
            
            logger.info(f"Saved conversation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            db.session.rollback()
    
    def get_conversation_history(self, user_id, limit=None):
        """Get conversation history for a user"""
        try:
            if limit is None:
                limit = self.max_history
            
            conversations = Conversation.query.filter_by(user_id=user_id)\
                .order_by(desc(Conversation.created_at))\
                .limit(limit)\
                .all()
            
            # Reverse to get chronological order
            return list(reversed(conversations))
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def clear_conversation_history(self, user_id):
        """Clear conversation history for a user"""
        try:
            Conversation.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            
            logger.info(f"Cleared conversation history for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            db.session.rollback()
            return False
    
    def get_user_language(self, user_id):
        """Get user's preferred language from recent conversations"""
        try:
            recent_conversation = Conversation.query.filter_by(user_id=user_id)\
                .order_by(desc(Conversation.created_at))\
                .first()
            
            if recent_conversation and recent_conversation.language:
                return recent_conversation.language
            
            return Config.DEFAULT_LANGUAGE
            
        except Exception as e:
            logger.error(f"Error getting user language: {e}")
            return Config.DEFAULT_LANGUAGE
    
    def set_user_language(self, user_id, language):
        """Set user's preferred language"""
        try:
            # Validate language
            if language not in Config.SUPPORTED_LANGUAGES:
                language = Config.DEFAULT_LANGUAGE
            
            # Create a system message to record language preference
            system_conversation = Conversation(
                user_id=user_id,
                user_name="System",
                message_type="system",
                user_message=f"/lang {language}",
                bot_response=f"Language set to {language}",
                language=language
            )
            
            db.session.add(system_conversation)
            db.session.commit()
            
            logger.info(f"Set language {language} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            db.session.rollback()
            return False
    
    def get_conversation_stats(self, user_id=None, days=7):
        """Get conversation statistics"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            query = Conversation.query.filter(Conversation.created_at >= since_date)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            conversations = query.all()
            
            stats = {
                'total_conversations': len(conversations),
                'message_types': {},
                'languages': {},
                'active_users': set(),
                'file_types': {}
            }
            
            for conv in conversations:
                # Count message types
                stats['message_types'][conv.message_type] = \
                    stats['message_types'].get(conv.message_type, 0) + 1
                
                # Count languages
                stats['languages'][conv.language] = \
                    stats['languages'].get(conv.language, 0) + 1
                
                # Count active users
                stats['active_users'].add(conv.user_id)
                
                # Count file types
                if conv.file_type:
                    stats['file_types'][conv.file_type] = \
                        stats['file_types'].get(conv.file_type, 0) + 1
            
            stats['active_users'] = len(stats['active_users'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}
    
    def cleanup_old_conversations(self, days=30):
        """Clean up old conversations to manage database size"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = Conversation.query.filter(
                Conversation.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old conversations")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            db.session.rollback()
            return 0
    
    def detect_and_update_language(self, user_id, user_message):
        """Detect language from user message and update if needed"""
        try:
            detected_lang = detect_language(user_message)
            current_lang = self.get_user_language(user_id)
            
            # Update language if detection is confident and different
            if detected_lang != current_lang and detected_lang in Config.SUPPORTED_LANGUAGES:
                self.set_user_language(user_id, detected_lang)
                return detected_lang
            
            return current_lang
            
        except Exception as e:
            logger.error(f"Error detecting/updating language: {e}")
            return Config.DEFAULT_LANGUAGE
