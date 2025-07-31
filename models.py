from app import db
from datetime import datetime
from sqlalchemy import Text, DateTime, Integer, String, Boolean, Index, event
from sqlalchemy.schema import CreateIndex
from sqlalchemy.ext.hybrid import hybrid_property
from utils.encryption import encryption_service

class Conversation(db.Model):
    """Store conversation context and history with PDPA compliance"""
    __tablename__ = 'conversations'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String(255), nullable=False, index=True)
    user_name = db.Column(String(255))  # Will be encrypted
    message_type = db.Column(String(50), nullable=False, index=True)  # text, image, file
    _user_message_encrypted = db.Column('user_message', Text)  # Encrypted storage
    _bot_response_encrypted = db.Column('bot_response', Text)  # Encrypted storage
    file_name = db.Column(String(255))
    file_type = db.Column(String(100), index=True)
    language = db.Column(String(10), default='en', index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
    # PDPA compliance fields
    user_id_hash = db.Column(String(32), index=True)  # Anonymized user ID for analytics
    data_classification = db.Column(String(20), default='confidential')  # Data sensitivity level
    consent_version = db.Column(String(10), default='1.0')  # Consent version when data was collected
    
    # Encrypted message properties
    @hybrid_property
    def user_message(self):
        """Decrypt user message on access"""
        if not self._user_message_encrypted:
            return None
        try:
            return encryption_service.decrypt_text(self._user_message_encrypted, self.data_classification)
        except Exception:
            return '[DECRYPTION_ERROR]'
    
    @user_message.setter
    def user_message(self, value):
        """Encrypt user message on storage"""
        if value is None:
            self._user_message_encrypted = None
        else:
            self._user_message_encrypted = encryption_service.encrypt_text(value, self.data_classification)
    
    @hybrid_property
    def bot_response(self):
        """Decrypt bot response on access"""
        if not self._bot_response_encrypted:
            return None
        try:
            return encryption_service.decrypt_text(self._bot_response_encrypted, self.data_classification)
        except Exception:
            return '[DECRYPTION_ERROR]'
    
    @bot_response.setter
    def bot_response(self, value):
        """Encrypt bot response on storage"""
        if value is None:
            self._bot_response_encrypted = None
        else:
            self._bot_response_encrypted = encryption_service.encrypt_text(value, self.data_classification)
    
    def anonymize_for_analytics(self):
        """Return anonymized version for analytics"""
        return {
            'id': self.id,
            'user_id_hash': self.user_id_hash or encryption_service.hash_user_id(self.user_id),
            'message_type': self.message_type,
            'user_message': encryption_service.anonymize_message(self.user_message, 'partial') if self.user_message else None,
            'bot_response': encryption_service.anonymize_message(self.bot_response, 'partial') if self.bot_response else None,
            'file_type': self.file_type,
            'language': self.language,
            'created_at': self.created_at
        }
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'created_at'),
        Index('idx_language_date', 'language', 'created_at'),
        Index('idx_message_type_date', 'message_type', 'created_at'),
        Index('idx_file_type_date', 'file_type', 'created_at'),
        Index('idx_user_lang_date', 'user_id', 'language', 'created_at'),
    )
    
class SystemLog(db.Model):
    """Store system logs and errors with privacy protection"""
    __tablename__ = 'system_logs'
    
    id = db.Column(Integer, primary_key=True)
    level = db.Column(String(20), nullable=False, index=True)
    message = db.Column(Text, nullable=False)
    user_id = db.Column(String(255), index=True)
    _error_details_encrypted = db.Column('error_details', Text)  # Encrypted sensitive error info
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
    # PDPA compliance fields
    user_id_hash = db.Column(String(32), index=True)  # Anonymized user ID
    data_classification = db.Column(String(20), default='internal')  # Usually internal level
    
    @hybrid_property
    def error_details(self):
        """Decrypt error details on access"""
        if not self._error_details_encrypted:
            return None
        try:
            return encryption_service.decrypt_text(self._error_details_encrypted, self.data_classification)
        except Exception:
            return '[DECRYPTION_ERROR]'
    
    @error_details.setter
    def error_details(self, value):
        """Encrypt error details on storage"""
        if value is None:
            self._error_details_encrypted = None
        else:
            self._error_details_encrypted = encryption_service.encrypt_text(value, self.data_classification)
    
    # Composite indexes for filtering and reporting
    __table_args__ = (
        Index('idx_level_date', 'level', 'created_at'),
        Index('idx_user_level_date', 'user_id', 'level', 'created_at'),
    )

class WebhookEvent(db.Model):
    """Store webhook events for monitoring with privacy protection"""
    __tablename__ = 'webhook_events'
    
    id = db.Column(Integer, primary_key=True)
    event_type = db.Column(String(100), nullable=False, index=True)
    user_id = db.Column(String(255), index=True)
    source_type = db.Column(String(50), index=True)  # user, group, room
    source_id = db.Column(String(255))
    message_id = db.Column(String(255), index=True)
    processed = db.Column(Boolean, default=False, index=True)
    processing_time = db.Column(Integer, index=True)  # milliseconds
    error_message = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
    # PDPA compliance fields
    user_id_hash = db.Column(String(32), index=True)  # Anonymized user ID for analytics
    data_classification = db.Column(String(20), default='internal')  # Usually internal level
    
    # Composite indexes for performance monitoring
    __table_args__ = (
        Index('idx_event_processed_date', 'event_type', 'processed', 'created_at'),
        Index('idx_user_event_date', 'user_id', 'event_type', 'created_at'),
        Index('idx_processed_time', 'processed', 'processing_time'),
        Index('idx_error_date', 'error_message', 'created_at'),
    )

class UserConsent(db.Model):
    """Track user consent for PDPA compliance"""
    __tablename__ = 'user_consents'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String(255), nullable=False, index=True)
    user_id_hash = db.Column(String(32), nullable=False, index=True)  # Anonymized version
    consent_type = db.Column(String(50), nullable=False, index=True)  # data_processing, analytics, marketing
    granted = db.Column(Boolean, nullable=False, index=True)
    purpose = db.Column(String(100), nullable=False)  # Purpose of data processing
    version = db.Column(String(10), default='1.0')  # Consent version
    ip_address = db.Column(String(45))  # IPv4/IPv6 address for audit
    user_agent = db.Column(String(500))  # Browser/client info for audit
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(DateTime)  # Consent expiration date
    
    # Composite indexes for consent management
    __table_args__ = (
        Index('idx_user_consent_type', 'user_id', 'consent_type'),
        Index('idx_user_hash_consent', 'user_id_hash', 'consent_type'),
        Index('idx_consent_expiry', 'expires_at', 'granted'),
    )
    
    def is_valid(self):
        """Check if consent is still valid"""
        if not self.granted:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

class DataProcessingLog(db.Model):
    """Log all data processing activities for PDPA audit trail"""
    __tablename__ = 'data_processing_logs'
    
    id = db.Column(Integer, primary_key=True)
    user_id_hash = db.Column(String(32), nullable=False, index=True)  # Only store anonymized ID
    activity_type = db.Column(String(50), nullable=False, index=True)  # create, read, update, delete, export
    data_category = db.Column(String(50), nullable=False, index=True)  # conversation, profile, analytics
    purpose = db.Column(String(100), nullable=False)  # Processing purpose
    legal_basis = db.Column(String(50), default='consent')  # consent, legitimate_interest, legal_obligation
    processor = db.Column(String(100))  # System/service that processed the data
    result = db.Column(String(20), default='success')  # success, error, partial
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_user_activity_date', 'user_id_hash', 'activity_type', 'created_at'),
        Index('idx_purpose_date', 'purpose', 'created_at'),
        Index('idx_data_category_date', 'data_category', 'created_at'),
    )

# Database performance optimization events
@event.listens_for(db.Model, 'before_bulk_insert')
def before_bulk_insert(query_context, query, query_dict, result):
    """Optimize bulk inserts by disabling autoflush"""
    db.session.autoflush = False

@event.listens_for(db.Model, 'after_bulk_insert')
def after_bulk_insert(query_context, query, query_dict, result):
    """Re-enable autoflush after bulk operations"""
    db.session.autoflush = True

# PDPA compliance event handlers
@event.listens_for(Conversation, 'before_insert')
def before_conversation_insert(mapper, connection, target):
    """Auto-populate PDPA fields before inserting conversation"""
    if not target.user_id_hash and target.user_id:
        target.user_id_hash = encryption_service.hash_user_id(target.user_id)

@event.listens_for(SystemLog, 'before_insert') 
def before_system_log_insert(mapper, connection, target):
    """Auto-populate PDPA fields before inserting system log"""
    if not target.user_id_hash and target.user_id:
        target.user_id_hash = encryption_service.hash_user_id(target.user_id)

@event.listens_for(WebhookEvent, 'before_insert')
def before_webhook_event_insert(mapper, connection, target):
    """Auto-populate PDPA fields before inserting webhook event"""
    if not target.user_id_hash and target.user_id:
        target.user_id_hash = encryption_service.hash_user_id(target.user_id)

@event.listens_for(UserConsent, 'before_insert')
def before_user_consent_insert(mapper, connection, target):
    """Auto-populate anonymized user ID for consent records"""
    if not target.user_id_hash and target.user_id:
        target.user_id_hash = encryption_service.hash_user_id(target.user_id)
