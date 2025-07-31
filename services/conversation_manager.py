import logging
from datetime import datetime, timedelta
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import Query, load_only
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
            from flask import has_app_context
            
            # Check if we're in application context
            if not has_app_context():
                logger.warning("save_conversation called outside application context, skipping save")
                return
            
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
            if has_app_context():
                db.session.rollback()
    
    def get_conversation_history(self, user_id, limit=None, include_system=False):
        """Get conversation history for a user with performance optimization"""
        try:
            if limit is None:
                limit = self.max_history
            
            # Optimized query with selective loading
            query = Conversation.query.filter_by(user_id=user_id)
            
            # Exclude system messages unless requested
            if not include_system:
                query = query.filter(Conversation.message_type != 'system')
            
            # Use index for efficient ordering and limiting
            conversations = query.order_by(desc(Conversation.created_at))\
                .limit(limit)\
                .options(load_only(
                    Conversation.id,
                    Conversation.user_message,
                    Conversation.bot_response,
                    Conversation.message_type,
                    Conversation.file_name,
                    Conversation.file_type,
                    Conversation.language,
                    Conversation.created_at
                ))\
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
        """Get user's preferred language from recent conversations - optimized"""
        try:
            from flask import has_app_context, current_app
            
            # Check if we're in application context
            if not has_app_context():
                # If not in context, return default language to avoid errors
                logger.warning("get_user_language called outside application context, returning default")
                return Config.DEFAULT_LANGUAGE
            
            # Use optimized query with specific column loading
            result = db.session.query(Conversation.language)\
                .filter_by(user_id=user_id)\
                .filter(Conversation.language.isnot(None))\
                .order_by(desc(Conversation.created_at))\
                .first()
            
            if result and result[0]:
                return result[0]
            
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
    
    def detect_and_update_language(self, user_id, message_text):
        """Detect language from message and update user preference if needed"""
        try:
            from flask import has_app_context
            
            if not has_app_context():
                logger.warning("detect_and_update_language called outside application context")
                return Config.DEFAULT_LANGUAGE
            
            # Get current user language
            current_lang = self.get_user_language(user_id)
            
            # Simple language detection logic
            detected_lang = detect_language(message_text) if message_text else current_lang
            
            # Update if different and detected language is supported
            if detected_lang != current_lang and detected_lang in Config.SUPPORTED_LANGUAGES:
                self.set_user_language(user_id, detected_lang)
                return detected_lang
            
            return current_lang
            
        except Exception as e:
            logger.error(f"Error detecting/updating language: {e}")
            return Config.DEFAULT_LANGUAGE
    
    def get_conversation_stats(self, user_id=None, days=7):
        """Get conversation statistics with optimized aggregation queries"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            base_filter = Conversation.created_at >= since_date
            if user_id:
                base_filter = and_(base_filter, Conversation.user_id == user_id)
            
            # Use database aggregation for better performance
            total_conversations = db.session.query(func.count(Conversation.id))\
                .filter(base_filter).scalar() or 0
            
            # Message type distribution
            message_types = dict(
                db.session.query(
                    Conversation.message_type,
                    func.count(Conversation.id)
                ).filter(base_filter)
                .group_by(Conversation.message_type)
                .all()
            )
            
            # Language distribution
            languages = dict(
                db.session.query(
                    Conversation.language,
                    func.count(Conversation.id)
                ).filter(base_filter)
                .group_by(Conversation.language)
                .all()
            )
            
            # Active users count
            active_users = db.session.query(func.count(func.distinct(Conversation.user_id)))\
                .filter(base_filter).scalar() or 0
            
            # File type distribution
            file_types = dict(
                db.session.query(
                    Conversation.file_type,
                    func.count(Conversation.id)
                ).filter(and_(base_filter, Conversation.file_type.isnot(None)))
                .group_by(Conversation.file_type)
                .all()
            )
            
            return {
                'total_conversations': total_conversations,
                'message_types': message_types,
                'languages': languages,
                'active_users': active_users,
                'file_types': file_types
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}
    
    def cleanup_old_conversations(self, days=30, batch_size=1000):
        """Clean up old conversations in batches to manage database size efficiently"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            total_deleted = 0
            
            while True:
                # Delete in batches to avoid locking the database
                deleted_count = db.session.query(Conversation)\
                    .filter(Conversation.created_at < cutoff_date)\
                    .limit(batch_size)\
                    .delete(synchronize_session=False)
                
                if deleted_count == 0:
                    break
                
                total_deleted += deleted_count
                db.session.commit()
                
                logger.info(f"Cleaned up batch of {deleted_count} conversations")
            
            logger.info(f"Total cleanup: {total_deleted} old conversations")
            return total_deleted
            
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
    
    def get_user_context_profile(self, user_id):
        """Get comprehensive user context for AI optimization - performance optimized"""
        try:
            # Get conversation count efficiently
            conversation_count = db.session.query(func.count(Conversation.id))\
                .filter_by(user_id=user_id).scalar() or 0
            
            # Get last interaction timestamp
            last_interaction = db.session.query(func.max(Conversation.created_at))\
                .filter_by(user_id=user_id).scalar()
            
            # Get recent message content for analysis
            recent_messages = db.session.query(Conversation.user_message)\
                .filter_by(user_id=user_id)\
                .filter(Conversation.user_message.isnot(None))\
                .order_by(desc(Conversation.created_at))\
                .limit(20)\
                .all()
            
            context_profile = {
                'user_id': user_id,
                'language': self.get_user_language(user_id),
                'conversation_count': conversation_count,
                'last_interaction': last_interaction,
                'common_topics': [],
                'business_type': None,
                'stage': None,
                'tier': 'free'  # Default tier
            }
            
            if recent_messages:
                # Analyze conversation patterns from recent messages
                messages = [msg[0].lower() for msg in recent_messages if msg[0]]
                
                # Simple topic detection
                business_keywords = {
                    'retail': ['ขาย', 'ร้าน', 'สินค้า', 'ลูกค้า', 'shop', 'sell', 'product'],
                    'food': ['อาหาร', 'ร้านอาหาร', 'เมนู', 'food', 'restaurant', 'menu'],
                    'manufacturing': ['ผลิต', 'โรงงาน', 'manufacture', 'factory', 'production'],
                    'services': ['บริการ', 'service', 'ให้บริการ', 'consultant']
                }
                
                for business_type, keywords in business_keywords.items():
                    if any(keyword in ' '.join(messages) for keyword in keywords):
                        context_profile['business_type'] = business_type
                        break
                
                # Stage detection
                stage_keywords = {
                    'startup': ['เริ่มต้น', 'startup', 'เปิดธุรกิจ', 'start business'],
                    'growth': ['ขยาย', 'expand', 'growth', 'เติบโต'],
                    'established': ['พัฒนา', 'develop', 'ปรับปรุง', 'improve']
                }
                
                for stage, keywords in stage_keywords.items():
                    if any(keyword in ' '.join(messages) for keyword in keywords):
                        context_profile['stage'] = stage
                        break
            
            return context_profile
            
        except Exception as e:
            logger.error(f"Error getting user context profile: {e}")
            return {
                'user_id': user_id,
                'language': Config.DEFAULT_LANGUAGE,
                'tier': 'free'
            }
    
    def get_conversation_context_summary(self, user_id, max_chars=500):
        """Get a compressed summary of conversation context for AI optimization - optimized"""
        try:
            # Get recent messages efficiently
            recent_messages = db.session.query(Conversation.user_message)\
                .filter_by(user_id=user_id)\
                .filter(Conversation.user_message.isnot(None))\
                .order_by(desc(Conversation.created_at))\
                .limit(5)\
                .all()
            
            if not recent_messages:
                return None
            
            # Extract key information
            topics = set()
            recent_questions = []
            
            for msg_tuple in recent_messages:
                if msg_tuple[0]:
                    msg = msg_tuple[0].lower()
                    
                    # Extract questions
                    if '?' in msg or any(q in msg for q in ['อย่างไร', 'ทำไง', 'how', 'what', 'why']):
                        recent_questions.append(msg[:100])
                    
                    # Extract topics
                    if any(keyword in msg for keyword in ['ธุรกิจ', 'business', 'การตลาด', 'marketing']):
                        topics.add('business_strategy')
                    if any(keyword in msg for keyword in ['การเงิน', 'finance', 'เงิน', 'money']):
                        topics.add('finance')
                    if any(keyword in msg for keyword in ['ภาษี', 'tax', 'บัญชี', 'accounting']):
                        topics.add('compliance')
            
            # Build summary
            summary_parts = []
            if topics:
                summary_parts.append(f"Topics: {', '.join(topics)}")
            if recent_questions:
                summary_parts.append(f"Recent questions: {len(recent_questions)} about business operations")
            
            summary = '. '.join(summary_parts)
            
            # Truncate if too long
            if len(summary) > max_chars:
                summary = summary[:max_chars-3] + '...'
            
            return summary if summary else None
            
        except Exception as e:
            logger.error(f"Error getting conversation context summary: {e}")
            return None
    
    def bulk_save_conversations(self, conversations_data):
        """Bulk save conversations for better performance"""
        try:
            if not conversations_data:
                return 0
            
            # Prepare conversation objects
            conversations = []
            for data in conversations_data:
                conv = Conversation(
                    user_id=data.get('user_id'),
                    user_name=data.get('user_name'),
                    message_type=data.get('message_type', 'text'),
                    user_message=data.get('user_message'),
                    bot_response=data.get('bot_response'),
                    file_name=data.get('file_name'),
                    file_type=data.get('file_type'),
                    language=data.get('language', Config.DEFAULT_LANGUAGE)
                )
                conversations.append(conv)
            
            # Bulk insert with optimized settings
            db.session.bulk_save_objects(conversations)
            db.session.commit()
            
            logger.info(f"Bulk saved {len(conversations)} conversations")
            return len(conversations)
            
        except Exception as e:
            logger.error(f"Error bulk saving conversations: {e}")
            db.session.rollback()
            return 0
    
    def optimize_database_performance(self):
        """Run database optimization tasks"""
        try:
            optimizations_applied = []
            
            # Analyze tables for PostgreSQL
            if 'postgresql' in db.engine.url.drivername:
                try:
                    db.session.execute("ANALYZE conversations;")
                    db.session.execute("ANALYZE system_logs;")
                    db.session.execute("ANALYZE webhook_events;")
                    db.session.commit()
                    optimizations_applied.append("PostgreSQL ANALYZE completed")
                except Exception as e:
                    logger.warning(f"Could not run ANALYZE: {e}")
            
            # Vacuum for SQLite
            elif 'sqlite' in db.engine.url.drivername:
                try:
                    db.session.execute("VACUUM;")
                    db.session.execute("PRAGMA optimize;")
                    db.session.commit()
                    optimizations_applied.append("SQLite VACUUM and OPTIMIZE completed")
                except Exception as e:
                    logger.warning(f"Could not run VACUUM: {e}")
            
            # Clean up old conversations automatically
            deleted_count = self.cleanup_old_conversations(days=90)
            if deleted_count > 0:
                optimizations_applied.append(f"Cleaned up {deleted_count} old conversations")
            
            logger.info(f"Database optimizations: {'; '.join(optimizations_applied)}")
            return optimizations_applied
            
        except Exception as e:
            logger.error(f"Error optimizing database performance: {e}")
            return []
    
    def get_database_health_metrics(self):
        """Get database health and performance metrics"""
        try:
            metrics = {}
            
            # Table sizes
            metrics['table_sizes'] = {}
            for table_name in ['conversations', 'system_logs', 'webhook_events']:
                count = db.session.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                metrics['table_sizes'][table_name] = count
            
            # Recent activity (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            metrics['recent_activity'] = {
                'conversations': db.session.query(func.count(Conversation.id))
                    .filter(Conversation.created_at >= last_24h).scalar() or 0,
                'unique_users': db.session.query(func.count(func.distinct(Conversation.user_id)))
                    .filter(Conversation.created_at >= last_24h).scalar() or 0
            }
            
            # Database size estimation
            if 'postgresql' in db.engine.url.drivername:
                try:
                    result = db.session.execute(
                        "SELECT pg_size_pretty(pg_database_size(current_database()))"
                    ).scalar()
                    metrics['database_size'] = result
                except Exception:
                    metrics['database_size'] = 'Unknown'
            elif 'sqlite' in db.engine.url.drivername:
                try:
                    import os
                    db_path = db.engine.url.database
                    if os.path.exists(db_path):
                        size_bytes = os.path.getsize(db_path)
                        metrics['database_size'] = f"{size_bytes / (1024*1024):.2f} MB"
                    else:
                        metrics['database_size'] = 'Unknown'
                except Exception:
                    metrics['database_size'] = 'Unknown'
            
            # Performance indicators
            metrics['performance'] = {
                'avg_conversations_per_user': 0,
                'most_active_language': Config.DEFAULT_LANGUAGE,
                'peak_usage_hour': 'Unknown'
            }
            
            # Calculate average conversations per user
            if metrics['recent_activity']['unique_users'] > 0:
                metrics['performance']['avg_conversations_per_user'] = round(
                    metrics['recent_activity']['conversations'] / metrics['recent_activity']['unique_users'], 2
                )
            
            # Most active language
            lang_stats = db.session.query(
                Conversation.language,
                func.count(Conversation.id)
            ).filter(Conversation.created_at >= last_24h)\
            .group_by(Conversation.language)\
            .order_by(func.count(Conversation.id).desc())\
            .first()
            
            if lang_stats:
                metrics['performance']['most_active_language'] = lang_stats[0]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting database health metrics: {e}")
            return {}
