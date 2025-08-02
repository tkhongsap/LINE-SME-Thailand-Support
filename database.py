import os
import logging
import threading
import time
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)

class DatabaseService:
    """Ultra-fast fire-and-forget logging service for Replit PostgreSQL"""
    
    def __init__(self):
        """Initialize direct database connection for optimal performance"""
        self.database_url = os.environ.get('DATABASE_URL')
        self.console_only = os.environ.get('CONSOLE_ONLY_LOGGING', 'false').lower() == 'true'
        
        if not self.database_url and not self.console_only:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Use direct connection instead of pooling for minimal overhead
        try:
            if self.console_only:
                logging.info("Console-only logging mode enabled for maximum performance")
            else:
                logging.info("Database direct connection service initialized")
                # Initialize schema with direct connection
                self._init_schema()
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    def _get_direct_connection(self):
        """Get direct database connection for optimal performance"""
        return psycopg2.connect(self.database_url)
    
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
            conn = self._get_direct_connection()
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            cursor.close()
            conn.close()
            logging.info("Database schema initialized")
            
        except Exception as e:
            logging.error(f"Schema initialization error: {e}")
    
    def log_conversation(self, user_id: str, message: str, response: str, 
                        response_time_ms: Optional[int] = None):
        """
        Ultra-fast fire-and-forget logging (console-only or database)
        
        Args:
            user_id: LINE user ID
            message: User's message
            response: Bot's response
            response_time_ms: Response time in milliseconds
        """
        if self.console_only:
            # Console-only logging for maximum performance
            logging.info(f"💬 {user_id[:10]}... | {response_time_ms}ms | {message[:30]}... → {response[:30]}...")
            return
        
        def _async_log():
            try:
                conn = self._get_direct_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    """INSERT INTO conversations (user_id, message, response, response_time_ms) 
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, message, response, response_time_ms)
                )
                
                conn.commit()
                cursor.close()
                conn.close()
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
            conn = self._get_direct_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
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