import logging
from datetime import datetime
from models import SystemLog
from app import db

class DatabaseHandler(logging.Handler):
    """Custom logging handler to store logs in database"""
    
    def emit(self, record):
        try:
            log_entry = SystemLog(
                level=record.levelname,
                message=record.getMessage(),
                user_id=getattr(record, 'user_id', None),
                error_details=getattr(record, 'error_details', None)
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            # Avoid recursive logging errors
            pass

def setup_logger(name):
    """Setup logger with both console and database handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Database handler
    db_handler = DatabaseHandler()
    db_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(db_handler)
    
    return logger

def log_user_interaction(user_id, message_type, user_message, bot_response, error=None):
    """Log user interactions for monitoring"""
    logger = logging.getLogger('user_interactions')
    
    log_data = {
        'user_id': user_id,
        'message_type': message_type,
        'user_message': user_message[:500] if user_message else None,  # Truncate long messages
        'bot_response': bot_response[:500] if bot_response else None,
    }
    
    if error:
        logger.error(f"User interaction error: {log_data}", extra={'user_id': user_id, 'error_details': str(error)})
    else:
        logger.info(f"User interaction: {log_data}", extra={'user_id': user_id})
