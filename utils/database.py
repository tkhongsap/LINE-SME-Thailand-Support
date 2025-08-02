import logging
import time
from functools import wraps
from sqlalchemy.exc import OperationalError, DisconnectionError, TimeoutError
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

def with_database_retry(max_retries=3, delay=1.0, backoff=2.0):
    """
    Decorator to retry database operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential delay
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError, TimeoutError) as e:
                    last_exception = e
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying in {current_delay} seconds...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                        
                        # Try to recover the database connection
                        try:
                            db.session.rollback()
                            db.session.close()
                            db.engine.dispose()
                        except Exception as recovery_error:
                            logger.warning(f"Connection recovery failed: {recovery_error}")
                    else:
                        logger.error(f"Database operation failed after {max_retries + 1} attempts")
                        raise last_exception
                except Exception as e:
                    # Non-recoverable exceptions are re-raised immediately
                    logger.error(f"Non-recoverable database error: {e}")
                    raise
            
            # This should not be reached, but just in case
            if last_exception:
                raise last_exception
            else:
                raise Exception("Unknown database error occurred")
        
        return wrapper
    return decorator

@with_database_retry(max_retries=2, delay=0.5)
def test_database_connection():
    """Test database connectivity with retry logic."""
    try:
        # Simple connectivity test
        result = db.session.execute(text("SELECT 1"))
        result.close()
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        db.session.rollback()
        raise

def get_database_status():
    """Get comprehensive database status information."""
    try:
        start_time = time.time()
        test_database_connection()
        response_time = time.time() - start_time
        
        # Get additional database info for PostgreSQL
        if hasattr(db.engine.url, 'drivername') and 'postgresql' in db.engine.url.drivername:
            try:
                version_result = db.session.execute(text("SELECT version()"))
                version = version_result.scalar()
                version_result.close()
                
                # Get connection count
                conn_result = db.session.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                ))
                connection_count = conn_result.scalar()
                conn_result.close()
                
                db.session.commit()
                
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'database_type': 'PostgreSQL',
                    'version': version,
                    'active_connections': connection_count
                }
            except Exception as e:
                logger.warning(f"Could not get detailed PostgreSQL info: {e}")
                db.session.rollback()
        
        return {
            'status': 'healthy',
            'response_time_ms': round(response_time * 1000, 2),
            'database_type': 'Connected'
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'database_type': 'Unknown'
        }

def ensure_database_connection():
    """Ensure database connection is active, recreate if necessary."""
    try:
        test_database_connection()
        return True
    except Exception as e:
        logger.warning(f"Database connection lost, attempting to reconnect: {e}")
        try:
            db.session.close()
            db.engine.dispose()
            # Test again after disposal
            test_database_connection()
            logger.info("Database connection successfully restored")
            return True
        except Exception as reconnect_error:
            logger.error(f"Failed to restore database connection: {reconnect_error}")
            return False