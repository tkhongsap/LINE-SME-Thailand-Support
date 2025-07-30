from app import db
from datetime import datetime
from sqlalchemy import Text, DateTime, Integer, String, Boolean

class Conversation(db.Model):
    """Store conversation context and history"""
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String(255), nullable=False, index=True)
    user_name = db.Column(String(255))
    message_type = db.Column(String(50), nullable=False)  # text, image, file
    user_message = db.Column(Text)
    bot_response = db.Column(Text)
    file_name = db.Column(String(255))
    file_type = db.Column(String(100))
    language = db.Column(String(10), default='en')
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
class SystemLog(db.Model):
    """Store system logs and errors"""
    id = db.Column(Integer, primary_key=True)
    level = db.Column(String(20), nullable=False)
    message = db.Column(Text, nullable=False)
    user_id = db.Column(String(255))
    error_details = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)

class WebhookEvent(db.Model):
    """Store webhook events for monitoring"""
    id = db.Column(Integer, primary_key=True)
    event_type = db.Column(String(100), nullable=False)
    user_id = db.Column(String(255))
    source_type = db.Column(String(50))  # user, group, room
    source_id = db.Column(String(255))
    message_id = db.Column(String(255))
    processed = db.Column(Boolean, default=False)
    processing_time = db.Column(Integer)  # milliseconds
    error_message = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
