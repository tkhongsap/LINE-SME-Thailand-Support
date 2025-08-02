"""
Flask application context utilities for handling database operations 
outside of request contexts (like async worker threads).
"""
import logging
from functools import wraps
from flask import current_app, has_app_context
from app import app

logger = logging.getLogger(__name__)

def with_app_context(func):
    """
    Decorator to ensure Flask application context is available for database operations.
    
    This is essential for async worker threads that operate outside the normal Flask request cycle.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if has_app_context():
            # Already in app context, proceed normally
            return func(*args, **kwargs)
        else:
            # Need to establish app context
            with app.app_context():
                return func(*args, **kwargs)
    
    return wrapper

def ensure_app_context():
    """
    Ensure we have an active Flask application context.
    Creates one if needed.
    
    Returns:
        bool: True if context is available, False otherwise
    """
    try:
        if has_app_context():
            return True
        else:
            # This will be handled by the decorator above
            logger.debug("No app context available - needs decorator")
            return False
    except Exception as e:
        logger.error(f"Error checking app context: {e}")
        return False

def get_user_language_safe(user_id=None, default_language='th'):
    """
    Safely get user language preference with proper Flask context handling.
    
    Args:
        user_id: User ID to look up language preference
        default_language: Default language if user preference not found
        
    Returns:
        str: Language code
    """
    try:
        if not has_app_context():
            logger.debug(f"get_user_language called outside application context, returning default: {default_language}")
            return default_language
            
        # Import here to avoid circular imports
        from models import User
        from app import db
        
        if user_id:
            try:
                user = db.session.query(User).filter_by(line_user_id=user_id).first()
                if user and hasattr(user, 'preferred_language') and user.preferred_language:
                    return user.preferred_language
            except Exception as query_error:
                logger.warning(f"Error querying user language: {query_error}")
                return default_language
                
        return default_language
        
    except Exception as e:
        logger.warning(f"Error getting user language for {user_id}: {e}")
        return default_language

def safe_database_operation(operation_func, *args, **kwargs):
    """
    Safely execute a database operation with proper context and error handling.
    
    Args:
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of the operation or None if failed
    """
    try:
        if not has_app_context():
            with app.app_context():
                return operation_func(*args, **kwargs)
        else:
            return operation_func(*args, **kwargs)
            
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        return None