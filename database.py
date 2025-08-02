import os
import logging
import threading
import time
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)

class DatabaseService:
    """Simplified async logging service for Replit PostgreSQL"""
    
    def __init__(self):
        """Initialize database connection using Replit's DATABASE_URL"""
        self.database_url = os.environ.get('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Create connection pool optimized for Replit
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,  # Minimum connections for Replit
                maxconn=5,  # Maximum connections for Replit constraints
                dsn=self.database_url
            )
            logging.info("Database connection pool initialized")
            
            # Initialize schema
            self._init_schema()
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    def _init_schema(self):
        """Create minimal database schema if not exists"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            response TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            response_time_ms INTEGER
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_created 
        ON conversations(user_id, created_at DESC);
        """
        
        try:
            conn = self.pool.getconn()
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            cursor.close()
            self.pool.putconn(conn)
            logging.info("Database schema initialized")
            
        except Exception as e:
            logging.error(f"Schema initialization error: {e}")
    
    def log_conversation(self, user_id: str, message: str, response: str, 
                        response_time_ms: Optional[int] = None):
        """
        Async log conversation to database (non-blocking)
        
        Args:
            user_id: LINE user ID
            message: User's message
            response: Bot's response
            response_time_ms: Response time in milliseconds
        """
        def _async_log():
            try:
                conn = self.pool.getconn()
                cursor = conn.cursor()
                
                cursor.execute(
                    """INSERT INTO conversations (user_id, message, response, response_time_ms) 
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, message, response, response_time_ms)
                )
                
                conn.commit()
                cursor.close()
                self.pool.putconn(conn)
                logging.info(f"Conversation logged for user: {user_id[:10]}...")
                
            except Exception as e:
                logging.error(f"Database logging error: {e}")
        
        # Execute in background thread (non-blocking)
        thread = threading.Thread(target=_async_log)
        thread.daemon = True
        thread.start()
    
    def health_check(self) -> bool:
        """Test database connectivity for health checks"""
        try:
            conn = self.pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            self.pool.putconn(conn)
            return result is not None
            
        except Exception as e:
            logging.error(f"Database health check error: {e}")
            return False

# Global instance for simplified usage
_db_service = None

def get_database_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

def log_conversation(user_id: str, message: str, response: str, 
                    response_time_ms: Optional[int] = None):
    """Simplified function for conversation logging"""
    service = get_database_service()
    service.log_conversation(user_id, message, response, response_time_ms)