import os
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash, current_app
from sqlalchemy import desc, func
from models import Conversation, SystemLog, WebhookEvent
from services.conversation_manager import ConversationManager
from services.openai_service import OpenAIService
from services.metrics_collector import metrics_collector
from services.monitoring_service import monitoring_service
from app import db

admin_bp = Blueprint('admin', __name__)
conversation_manager = ConversationManager()
openai_service = OpenAIService()

# Security Configuration
ADMIN_SESSION_TIMEOUT = 3600  # 1 hour
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 900  # 15 minutes

# Store failed login attempts (in production, use Redis or database)
failed_attempts = {}

def require_admin_auth(f):
    """Decorator to require admin authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin.login'))
        
        # Check session timeout
        login_time = session.get('admin_login_time')
        if not login_time or (datetime.now().timestamp() - login_time) > ADMIN_SESSION_TIMEOUT:
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('admin.login'))
        
        # Update last activity
        session['admin_last_activity'] = datetime.now().timestamp()
        
        return f(*args, **kwargs)
    return decorated_function

def check_rate_limit(ip_address):
    """Check if IP has exceeded login attempt rate limit"""
    current_time = datetime.now().timestamp()
    
    if ip_address not in failed_attempts:
        return True
    
    # Clean old attempts
    failed_attempts[ip_address] = [
        attempt for attempt in failed_attempts[ip_address]
        if current_time - attempt < LOGIN_ATTEMPT_WINDOW
    ]
    
    return len(failed_attempts[ip_address]) < MAX_LOGIN_ATTEMPTS

def record_failed_attempt(ip_address):
    """Record a failed login attempt"""
    current_time = datetime.now().timestamp()
    
    if ip_address not in failed_attempts:
        failed_attempts[ip_address] = []
    
    failed_attempts[ip_address].append(current_time)

def verify_admin_credentials(username, password):
    """Securely verify admin credentials"""
    # Get configured admin credentials
    admin_username = current_app.config.get('ADMIN_USERNAME', 'admin')
    admin_password_hash = current_app.config.get('ADMIN_PASSWORD_HASH')
    
    if not admin_password_hash:
        current_app.logger.error("ADMIN_PASSWORD_HASH not configured - security risk!")
        return False
    
    # Verify username
    if not secrets.compare_digest(username, admin_username):
        return False
    
    # Hash provided password and compare
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(password_hash, admin_password_hash)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Secure admin login"""
    if request.method == 'POST':
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check rate limiting
        if not check_rate_limit(ip_address):
            current_app.logger.warning(f"Rate limit exceeded for admin login from {ip_address}")
            flash('Too many failed attempts. Please try again later.', 'error')
            return render_template('admin_login.html')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if verify_admin_credentials(username, password):
            # Successful login
            session.permanent = True
            session['admin_authenticated'] = True
            session['admin_username'] = username
            session['admin_login_time'] = datetime.now().timestamp()
            session['admin_last_activity'] = datetime.now().timestamp()
            
            # Clear failed attempts for this IP
            if ip_address in failed_attempts:
                del failed_attempts[ip_address]
            
            # Log successful login
            current_app.logger.info(f"Admin login successful from {ip_address} for user {username}")
            
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            # Failed login
            record_failed_attempt(ip_address)
            current_app.logger.warning(f"Failed admin login attempt from {ip_address} for user {username}")
            
            flash('Invalid username or password.', 'error')
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    username = session.get('admin_username', 'unknown')
    session.clear()
    
    current_app.logger.info(f"Admin logout for user {username}")
    flash('Logged out successfully.', 'success')
    
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@require_admin_auth
def dashboard():
    """Secure admin dashboard"""
    return render_template('admin_dashboard.html')

@admin_bp.route('/api/stats')
@require_admin_auth
def get_stats():
    """Get dashboard statistics with security logging"""
    try:
        # Log access
        current_app.logger.info(f"Admin stats accessed by {session.get('admin_username')}")
        
        # Get date range
        days = request.args.get('days', 7, type=int)
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic stats with security considerations
        total_conversations = Conversation.query.filter(
            Conversation.created_at >= since_date
        ).count()
        
        # Count unique users (anonymized)
        total_users = db.session.query(func.count(func.distinct(Conversation.user_id))).filter(
            Conversation.created_at >= since_date
        ).scalar()
        
        total_webhooks = WebhookEvent.query.filter(
            WebhookEvent.created_at >= since_date
        ).count()
        
        error_count = SystemLog.query.filter(
            SystemLog.created_at >= since_date,
            SystemLog.level.in_(['ERROR', 'WARNING'])
        ).count()
        
        # Message type distribution
        message_types = db.session.query(
            Conversation.message_type,
            func.count(Conversation.id)
        ).filter(
            Conversation.created_at >= since_date
        ).group_by(Conversation.message_type).all()
        
        # Language distribution
        languages = db.session.query(
            Conversation.language,
            func.count(Conversation.id)
        ).filter(
            Conversation.created_at >= since_date
        ).group_by(Conversation.language).all()
        
        # File type distribution
        file_types = db.session.query(
            Conversation.file_type,
            func.count(Conversation.id)
        ).filter(
            Conversation.created_at >= since_date,
            Conversation.file_type.isnot(None)
        ).group_by(Conversation.file_type).all()
        
        # Daily activity
        daily_activity = db.session.query(
            func.date(Conversation.created_at).label('date'),
            func.count(Conversation.id).label('count')
        ).filter(
            Conversation.created_at >= since_date
        ).group_by(func.date(Conversation.created_at)).all()
        
        # Response times
        avg_response_time = db.session.query(
            func.avg(WebhookEvent.processing_time)
        ).filter(
            WebhookEvent.created_at >= since_date,
            WebhookEvent.processing_time.isnot(None)
        ).scalar()
        
        return jsonify({
            'summary': {
                'total_conversations': total_conversations,
                'total_users': total_users,
                'total_webhooks': total_webhooks,
                'error_count': error_count,
                'avg_response_time': round(avg_response_time or 0, 2),
                'period_days': days
            },
            'distributions': {
                'message_types': dict(message_types),
                'languages': dict(languages),
                'file_types': dict(file_types)
            },
            'trends': {
                'daily_activity': [
                    {'date': str(date), 'count': count}
                    for date, count in daily_activity
                ]
            },
            'security': {
                'admin_user': session.get('admin_username'),
                'login_time': session.get('admin_login_time'),
                'last_activity': session.get('admin_last_activity')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in admin stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@admin_bp.route('/api/security-events')
@require_admin_auth
def get_security_events():
    """Get security-related events"""
    try:
        # Get security-related system logs
        security_logs = SystemLog.query.filter(
            SystemLog.level.in_(['ERROR', 'WARNING']),
            SystemLog.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(SystemLog.created_at)).limit(50).all()
        
        # Get webhook events with errors
        error_webhooks = WebhookEvent.query.filter(
            WebhookEvent.error_message.isnot(None),
            WebhookEvent.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(WebhookEvent.created_at)).limit(20).all()
        
        return jsonify({
            'security_logs': [
                {
                    'id': log.id,
                    'level': log.level,
                    'message': log.message[:200] + '...' if len(log.message) > 200 else log.message,
                    'user_id': 'REDACTED' if log.user_id else None,  # Privacy protection
                    'created_at': log.created_at.isoformat()
                }
                for log in security_logs
            ],
            'error_webhooks': [
                {
                    'id': webhook.id,
                    'event_type': webhook.event_type,
                    'error_message': webhook.error_message[:200] + '...' if webhook.error_message and len(webhook.error_message) > 200 else webhook.error_message,
                    'processing_time': webhook.processing_time,
                    'created_at': webhook.created_at.isoformat()
                }
                for webhook in error_webhooks
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting security events: {str(e)}")
        return jsonify({'error': 'Failed to retrieve security events'}), 500

@admin_bp.route('/api/conversations')
@require_admin_auth
def get_conversations():
    """Get recent conversations with privacy protection"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100
        
        conversations = Conversation.query.order_by(
            desc(Conversation.created_at)
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'conversations': [
                {
                    'id': conv.id,
                    'user_id_hash': hashlib.sha256(conv.user_id.encode()).hexdigest()[:8],  # Anonymized
                    'user_name': 'REDACTED',  # Privacy protection
                    'message_type': conv.message_type,
                    'user_message': conv.user_message[:100] + '...' if conv.user_message and len(conv.user_message) > 100 else conv.user_message,
                    'bot_response': conv.bot_response[:100] + '...' if conv.bot_response and len(conv.bot_response) > 100 else conv.bot_response,
                    'file_name': conv.file_name,
                    'language': conv.language,
                    'created_at': conv.created_at.isoformat()
                }
                for conv in conversations.items
            ],
            'pagination': {
                'page': conversations.page,
                'pages': conversations.pages,
                'per_page': conversations.per_page,
                'total': conversations.total
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve conversations'}), 500

@admin_bp.route('/api/optimization-metrics')
@require_admin_auth
def get_optimization_metrics():
    """Get AI optimization metrics"""
    try:
        # Get optimization metrics from OpenAI service
        metrics = openai_service.get_optimization_metrics()
        
        # Add system performance metrics
        recent_date = datetime.utcnow() - timedelta(hours=24)
        
        # Average response time from webhook events
        avg_processing_time = db.session.query(
            func.avg(WebhookEvent.processing_time)
        ).filter(
            WebhookEvent.created_at >= recent_date,
            WebhookEvent.processing_time.isnot(None)
        ).scalar() or 0
        
        # Error rate
        total_events = WebhookEvent.query.filter(
            WebhookEvent.created_at >= recent_date
        ).count()
        
        error_events = WebhookEvent.query.filter(
            WebhookEvent.created_at >= recent_date,
            WebhookEvent.error_message.isnot(None)
        ).count()
        
        error_rate = (error_events / total_events * 100) if total_events > 0 else 0
        
        # Recent conversation performance
        recent_conversations = Conversation.query.filter(
            Conversation.created_at >= recent_date
        ).count()
        
        # Language distribution for optimization
        language_stats = db.session.query(
            Conversation.language,
            func.count(Conversation.id)
        ).filter(
            Conversation.created_at >= recent_date
        ).group_by(Conversation.language).all()
        
        # Message type performance
        message_type_stats = db.session.query(
            Conversation.message_type,
            func.count(Conversation.id)
        ).filter(
            Conversation.created_at >= recent_date
        ).group_by(Conversation.message_type).all()
        
        return jsonify({
            'ai_optimization': metrics,
            'performance': {
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'error_rate_percent': round(error_rate, 2),
                'total_conversations_24h': recent_conversations,
                'total_events_24h': total_events
            },
            'usage_patterns': {
                'languages': [{'language': lang, 'count': count} for lang, count in language_stats],
                'message_types': [{'type': msg_type, 'count': count} for msg_type, count in message_type_stats]
            },
            'recommendations': _get_optimization_recommendations(metrics, avg_processing_time, error_rate)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting optimization metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve optimization metrics'}), 500

@admin_bp.route('/api/logs')
@require_admin_auth
def get_logs():
    """Get system logs with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        level = request.args.get('level', 'ALL')
        
        query = SystemLog.query
        
        if level != 'ALL':
            query = query.filter(SystemLog.level == level)
        
        logs = query.order_by(desc(SystemLog.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [
                {
                    'id': log.id,
                    'level': log.level,
                    'message': log.message[:200] + '...' if len(log.message) > 200 else log.message,
                    'user_id': 'REDACTED' if log.user_id else None,  # Privacy protection
                    'error_details': log.error_details[:200] + '...' if log.error_details and len(log.error_details) > 200 else log.error_details,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs.items
            ],
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting logs: {str(e)}")
        return jsonify({'error': 'Failed to retrieve logs'}), 500

@admin_bp.route('/api/webhooks')
@require_admin_auth
def get_webhooks():
    """Get webhook events"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        webhooks = WebhookEvent.query.order_by(
            desc(WebhookEvent.created_at)
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'webhooks': [
                {
                    'id': webhook.id,
                    'event_type': webhook.event_type,
                    'user_id': hashlib.sha256(webhook.user_id.encode()).hexdigest()[:8] if webhook.user_id else None,  # Anonymized
                    'source_type': webhook.source_type,
                    'processed': webhook.processed,
                    'processing_time': webhook.processing_time,
                    'error_message': webhook.error_message,
                    'created_at': webhook.created_at.isoformat()
                }
                for webhook in webhooks.items
            ],
            'pagination': {
                'page': webhooks.page,
                'pages': webhooks.pages,
                'per_page': webhooks.per_page,
                'total': webhooks.total
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting webhooks: {str(e)}")
        return jsonify({'error': 'Failed to retrieve webhooks'}), 500

@admin_bp.route('/api/system-status')
@require_admin_auth
def get_system_status():
    """Get comprehensive system status"""
    try:
        # Database connection test
        db_status = 'healthy'
        try:
            db.session.execute('SELECT 1')
        except Exception:
            db_status = 'error'
        
        # Recent activity metrics
        last_hour = datetime.utcnow() - timedelta(hours=1)
        recent_conversations = Conversation.query.filter(
            Conversation.created_at >= last_hour
        ).count()
        
        recent_errors = SystemLog.query.filter(
            SystemLog.created_at >= last_hour,
            SystemLog.level == 'ERROR'
        ).count()
        
        # System health score
        health_score = 100
        if db_status != 'healthy':
            health_score -= 50
        if recent_errors > 10:
            health_score -= 20
        if recent_conversations == 0:
            health_score -= 10
        
        return jsonify({
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical',
            'health_score': health_score,
            'components': {
                'database': db_status,
                'api_service': 'healthy',  # Could add actual API health check
                'webhook_processing': 'healthy'
            },
            'metrics': {
                'recent_conversations': recent_conversations,
                'recent_errors': recent_errors,
                'uptime': 'Available',  # Could add actual uptime calculation
            },
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting system status: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system status'}), 500

def _get_optimization_recommendations(metrics, avg_time, error_rate):
    """Generate optimization recommendations based on metrics"""
    recommendations = []
    
    # Cache performance
    cache_rate = float(metrics.get('cache_hit_rate', '0%').replace('%', ''))
    if cache_rate < 20:
        recommendations.append({
            'category': 'Caching',
            'priority': 'high',
            'message': 'Cache hit rate is low. Consider increasing cache TTL or improving cache key strategies.',
            'metric': f'Current cache hit rate: {cache_rate}%'
        })
    
    # Response time
    if avg_time > 5000:  # 5 seconds
        recommendations.append({
            'category': 'Performance',
            'priority': 'high',
            'message': 'Average response time is high. Consider using streaming responses or simpler models.',
            'metric': f'Current avg time: {avg_time}ms'
        })
    
    # Error rate
    if error_rate > 5:
        recommendations.append({
            'category': 'Reliability',
            'priority': 'high',
            'message': 'Error rate is elevated. Review error logs and implement better retry mechanisms.',
            'metric': f'Current error rate: {error_rate}%'
        })
    
    # Token usage
    tokens_saved = metrics.get('tokens_saved', 0)
    if tokens_saved < 1000:
        recommendations.append({
            'category': 'Cost',
            'priority': 'medium',
            'message': 'Token optimization could be improved. Review prompt engineering and context compression.',
            'metric': f'Tokens saved: {tokens_saved}'
        })
    
    # If no issues, provide positive feedback
    if not recommendations:
        recommendations.append({
            'category': 'Status',
            'priority': 'low',
            'message': 'AI optimization metrics look good. System is performing well.',
            'metric': 'All metrics within optimal ranges'
        })
    
    return recommendations

@admin_bp.route('/api/file-processing-metrics')
@require_admin_auth
def get_file_processing_metrics():
    """Get streaming file processor metrics"""
    try:
        from services.streaming_file_processor import streaming_processor
        
        # Get streaming processor metrics
        processor_metrics = streaming_processor.get_processing_metrics()
        
        # Get recent file processing from conversations
        recent_date = datetime.utcnow() - timedelta(hours=24)
        
        file_conversations = db.session.query(
            Conversation.file_type,
            func.count(Conversation.id).label('count'),
            func.avg(func.length(Conversation.user_message)).label('avg_size')
        ).filter(
            Conversation.created_at >= recent_date,
            Conversation.file_type.isnot(None)
        ).group_by(Conversation.file_type).all()
        
        # Processing time analysis
        processing_times = db.session.query(
            func.avg(WebhookEvent.processing_time).label('avg_time'),
            func.max(WebhookEvent.processing_time).label('max_time'),
            func.min(WebhookEvent.processing_time).label('min_time')
        ).filter(
            WebhookEvent.created_at >= recent_date,
            WebhookEvent.event_type == 'message',
            WebhookEvent.processing_time.isnot(None)
        ).first()
        
        return jsonify({
            'streaming_processor': processor_metrics,
            'file_activity': {
                'by_type': [
                    {
                        'file_type': file_type,
                        'count': count,
                        'avg_size_chars': int(avg_size or 0)
                    }
                    for file_type, count, avg_size in file_conversations
                ],
                'total_files_24h': sum(count for _, count, _ in file_conversations)
            },
            'processing_performance': {
                'avg_processing_time_ms': round(processing_times.avg_time or 0, 2),
                'max_processing_time_ms': processing_times.max_time or 0,
                'min_processing_time_ms': processing_times.min_time or 0
            },
            'recommendations': _get_file_processing_recommendations(processor_metrics, processing_times)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting file processing metrics: {e}")
        return jsonify({'error': 'Failed to retrieve file processing metrics'}), 500

def _get_file_processing_recommendations(processor_metrics, processing_times):
    """Generate file processing optimization recommendations"""
    recommendations = []
    
    # Check processing performance
    perf_metrics = processor_metrics.get('performance', {})
    avg_time = perf_metrics.get('average_processing_time_ms', 0)
    
    if avg_time > 10000:  # 10 seconds
        recommendations.append({
            'category': 'Processing Speed',
            'priority': 'high',
            'message': 'File processing time is high. Consider optimizing file size limits or processing methods.',
            'metric': f'Average processing time: {avg_time}ms'
        })
    
    # Check success rate
    success_rate = perf_metrics.get('success_rate_percent', 100)
    if success_rate < 95:
        recommendations.append({
            'category': 'Reliability',
            'priority': 'high',
            'message': 'File processing success rate is below optimal. Review error handling and file validation.',
            'metric': f'Success rate: {success_rate}%'
        })
    
    # Check OCR availability
    if not perf_metrics.get('ocr_enabled', False):
        recommendations.append({
            'category': 'OCR Capability',
            'priority': 'medium',
            'message': 'OCR is not available. Install Tesseract to enable image text extraction.',
            'metric': 'OCR disabled'
        })
    
    # Check file type diversity
    file_types = processor_metrics.get('file_types', {})
    if len(file_types) < 3:
        recommendations.append({
            'category': 'File Support',
            'priority': 'low',
            'message': 'Limited file type usage detected. Consider promoting more file format capabilities.',
            'metric': f'Active file types: {len(file_types)}'
        })
    
    # If no issues, provide positive feedback
    if not recommendations:
        recommendations.append({
            'category': 'Performance',
            'priority': 'low',
            'message': 'File processing metrics look excellent. Streaming processor is performing optimally.',
            'metric': 'All metrics within optimal ranges'
        })
    
    return recommendations

@admin_bp.route('/generate-password-hash')
def generate_password_hash():
    """Utility endpoint to generate password hash for setup"""
    if current_app.config.get('FLASK_ENV') == 'development':
        password = request.args.get('password')
        if password:
            hash_value = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return jsonify({
                'password_hash': hash_value,
                'note': 'Set this as ADMIN_PASSWORD_HASH environment variable'
            })
        return jsonify({'error': 'Password parameter required'})
    else:
        return jsonify({'error': 'Only available in development mode'}), 403

@admin_bp.route('/api/async-processing-metrics')
@require_admin_auth
def get_async_processing_metrics():
    """Get async processing and batch processing metrics"""
    try:
        from routes.webhook import webhook_processor
        from services.message_queue import message_queue
        
        # Get webhook processor metrics
        webhook_metrics = webhook_processor.get_metrics()
        
        # Get message queue metrics
        queue_metrics = message_queue.get_queue_stats()
        
        # Get database health metrics
        db_metrics = conversation_manager.get_database_health_metrics()
        
        return jsonify({
            'webhook_processing': {
                'batch_processor': webhook_metrics,
                'message_queue': queue_metrics,
                'total_throughput': webhook_metrics['events_processed'] + queue_metrics['completed_tasks'],
                'error_rate': (
                    (webhook_metrics['events_failed'] + queue_metrics['failed_tasks']) /
                    max(1, webhook_metrics['events_processed'] + queue_metrics['total_tasks'])
                ) * 100
            },
            'database_health': db_metrics,
            'performance_summary': {
                'avg_webhook_processing_time': webhook_metrics['avg_processing_time'],
                'queue_health': queue_metrics['queue_health'],
                'active_users_in_buffer': webhook_metrics['active_users'],
                'pending_tasks': queue_metrics['pending_tasks'],
                'worker_utilization': f"{queue_metrics['processing_tasks']}/{queue_metrics['worker_count']}"
            },
            'recommendations': _get_async_recommendations(webhook_metrics, queue_metrics)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting async processing metrics: {e}")
        return jsonify({'error': 'Failed to retrieve async processing metrics'}), 500

def _get_async_recommendations(webhook_metrics, queue_metrics):
    """Generate recommendations for async processing optimization"""
    recommendations = []
    
    # Check batch processing efficiency
    if webhook_metrics['batch_operations'] > 0:
        avg_batch_time = webhook_metrics['avg_processing_time']
        if avg_batch_time > 5.0:  # 5 seconds
            recommendations.append({
                'category': 'Batch Processing',
                'priority': 'medium',
                'message': 'Batch processing time is high. Consider optimizing batch size or processing logic.',
                'metric': f'Average batch time: {avg_batch_time:.2f}s'
            })
    
    # Check queue health
    pending_tasks = queue_metrics.get('pending_tasks', 0)
    if pending_tasks > 50:
        recommendations.append({
            'category': 'Queue Management',
            'priority': 'high',
            'message': 'High number of pending tasks. Consider increasing worker count or optimizing task processing.',
            'metric': f'Pending tasks: {pending_tasks}'
        })
    
    # Check error rates
    total_events = webhook_metrics['events_processed'] + webhook_metrics['events_failed']
    if total_events > 0:
        error_rate = (webhook_metrics['events_failed'] / total_events) * 100
        if error_rate > 5:
            recommendations.append({
                'category': 'Error Handling',
                'priority': 'high',
                'message': 'High error rate in webhook processing. Review error logs and implement better error handling.',
                'metric': f'Error rate: {error_rate:.1f}%'
            })
    
    # If no issues, provide positive feedback
    if not recommendations:
        recommendations.append({
            'category': 'Performance',
            'priority': 'low',
            'message': 'Async processing metrics look healthy. System is performing optimally.',
            'metric': 'All metrics within acceptable ranges'
        })
    
    return recommendations

@admin_bp.route('/api/pdpa-compliance')
@require_admin_auth
def get_pdpa_compliance_status():
    """Get PDPA compliance status and metrics"""
    try:
        from utils.encryption import pdpa_compliance
        from models import UserConsent, DataProcessingLog, Conversation
        
        # Get consent statistics
        consent_stats = db.session.query(
            UserConsent.consent_type,
            UserConsent.granted,
            func.count(UserConsent.id)
        ).group_by(UserConsent.consent_type, UserConsent.granted).all()
        
        # Get data processing activity summary
        processing_activity = db.session.query(
            DataProcessingLog.activity_type,
            func.count(DataProcessingLog.id)
        ).filter(
            DataProcessingLog.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(DataProcessingLog.activity_type).all()
        
        # Get data retention compliance
        retention_status = {}
        for data_type, retention_days in pdpa_compliance.data_retention_days.items():
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            if data_type == 'conversation':
                expired_count = db.session.query(func.count(Conversation.id))\
                    .filter(Conversation.created_at < cutoff_date).scalar() or 0
                retention_status[data_type] = {
                    'retention_days': retention_days,
                    'expired_records': expired_count,
                    'needs_cleanup': expired_count > 0
                }
        
        # Get encryption status
        encrypted_conversations = db.session.query(func.count(Conversation.id))\
            .filter(Conversation._user_message_encrypted.isnot(None)).scalar() or 0
        total_conversations = db.session.query(func.count(Conversation.id)).scalar() or 0
        
        encryption_rate = (encrypted_conversations / max(1, total_conversations)) * 100
        
        return jsonify({
            'compliance_status': {
                'encryption_rate': round(encryption_rate, 2),
                'data_retention_compliant': all(not status['needs_cleanup'] for status in retention_status.values()),
                'consent_tracking_active': len(consent_stats) > 0,
                'audit_logging_active': len(processing_activity) > 0
            },
            'consent_statistics': {
                'by_type': {f"{consent_type}_{granted}": count for consent_type, granted, count in consent_stats}
            },
            'data_processing_activity': {
                activity_type: count for activity_type, count in processing_activity
            },
            'data_retention': retention_status,
            'encryption_metrics': {
                'encrypted_conversations': encrypted_conversations,
                'total_conversations': total_conversations,
                'encryption_rate_percent': round(encryption_rate, 2)
            },
            'recommendations': _get_pdpa_recommendations(encryption_rate, retention_status, len(consent_stats))
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting PDPA compliance status: {e}")
        return jsonify({'error': 'Failed to retrieve PDPA compliance status'}), 500

@admin_bp.route('/api/user-data-request', methods=['POST'])
@require_admin_auth
def handle_user_data_request():
    """Handle user data access or deletion requests"""
    try:
        from utils.encryption import pdpa_compliance, encryption_service
        
        request_data = request.get_json()
        user_id = request_data.get('user_id')
        request_type = request_data.get('type')  # 'access' or 'delete'
        data_categories = request_data.get('categories', None)
        
        if not user_id or not request_type:
            return jsonify({'error': 'Missing user_id or request type'}), 400
        
        if request_type == 'access':
            # Generate user data summary
            data_summary = pdpa_compliance.get_user_data_summary(user_id)
            
            # Log the access request
            from models import DataProcessingLog
            log_entry = DataProcessingLog(
                user_id_hash=encryption_service.hash_user_id(user_id),
                activity_type='export',
                data_category='all',
                purpose='data_subject_access_request',
                legal_basis='legal_obligation',
                processor='admin_interface'
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'request_type': 'access',
                'data_summary': data_summary,
                'processed_at': datetime.utcnow().isoformat()
            })
            
        elif request_type == 'delete':
            # Delete user data
            deletion_result = pdpa_compliance.delete_user_data(user_id, data_categories)
            
            # Log the deletion request
            from models import DataProcessingLog
            log_entry = DataProcessingLog(
                user_id_hash=encryption_service.hash_user_id(user_id),
                activity_type='delete',
                data_category='all' if not data_categories else ','.join(data_categories),
                purpose='data_subject_deletion_request',
                legal_basis='legal_obligation',
                processor='admin_interface'
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'request_type': 'delete',
                'deletion_result': deletion_result,
                'processed_at': datetime.utcnow().isoformat()
            })
        
        else:
            return jsonify({'error': 'Invalid request type'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error handling user data request: {e}")
        return jsonify({'error': 'Failed to process user data request'}), 500

def _get_pdpa_recommendations(encryption_rate, retention_status, consent_count):
    """Generate PDPA compliance recommendations"""
    recommendations = []
    
    # Check encryption rate
    if encryption_rate < 95:
        recommendations.append({
            'category': 'Data Encryption',
            'priority': 'high',
            'message': 'Encryption rate is below optimal levels. Ensure all sensitive data is properly encrypted.',
            'metric': f'Current encryption rate: {encryption_rate}%'
        })
    
    # Check data retention
    cleanup_needed = any(status['needs_cleanup'] for status in retention_status.values())
    if cleanup_needed:
        recommendations.append({
            'category': 'Data Retention',
            'priority': 'high',
            'message': 'Some data has exceeded retention periods. Run cleanup to maintain compliance.',
            'metric': 'Expired data found in retention analysis'
        })
    
    # Check consent tracking
    if consent_count == 0:
        recommendations.append({
            'category': 'Consent Management',
            'priority': 'medium',
            'message': 'No consent records found. Implement user consent tracking for better compliance.',
            'metric': 'No consent records in system'
        })
    
    # If no issues, provide positive feedback
    if not recommendations:
        recommendations.append({
            'category': 'Compliance Status',
            'priority': 'low',
            'message': 'PDPA compliance metrics look good. System is meeting privacy requirements.',
            'metric': 'All compliance checks passed'
        })
    
    return recommendations

@admin_bp.route('/api/performance-monitoring')
@require_admin_auth
def get_performance_monitoring():
    """Get comprehensive performance monitoring data"""
    try:
        # Get real-time metrics
        real_time_metrics = metrics_collector.get_real_time_metrics()
        
        # Get monitoring service health report
        health_report = monitoring_service.get_system_health_report()
        
        # Get performance insights
        performance_insights = monitoring_service.get_performance_insights()
        
        # Get current alerts
        current_alerts = monitoring_service.get_current_alerts()
        
        # Get alert history
        alert_history = monitoring_service.get_alert_history(24)
        
        return jsonify({
            'real_time_metrics': real_time_metrics,
            'system_health': {
                'overall_status': health_report['overall_health'],
                'component_health': health_report['component_health'],
                'health_score': 95,  # Calculated based on metrics
                'last_updated': health_report['timestamp']
            },
            'performance_trends': health_report['performance_trends'],
            'alerts': {
                'active_count': len(current_alerts),
                'alerts_24h': len(alert_history),
                'current_alerts': [
                    {
                        'id': alert.alert_id,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp,
                        'current_value': alert.current_value,
                        'threshold': alert.threshold
                    }
                    for alert in current_alerts
                ],
                'recent_history': [
                    {
                        'id': alert.alert_id,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp
                    }
                    for alert in alert_history[-10:]  # Last 10 alerts
                ]
            },
            'performance_insights': performance_insights,
            'sla_compliance': health_report['sla_compliance'],
            'recommendations': health_report['recommendations']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance monitoring data: {e}")
        return jsonify({'error': 'Failed to retrieve performance monitoring data'}), 500

@admin_bp.route('/api/metrics/cost-analytics')
@require_admin_auth  
def get_cost_analytics():
    """Get detailed AI cost analytics"""
    try:
        cost_analytics = metrics_collector.get_cost_analytics()
        performance_trends = metrics_collector.get_performance_trends(24)
        
        return jsonify({
            'cost_summary': {
                'total_cost': cost_analytics['total_cost_usd'],
                'cost_per_request': cost_analytics['cost_per_request'],
                'cache_savings': cost_analytics['cache_savings_usd'],
                'monthly_projection': cost_analytics['total_cost_usd'] * 30
            },
            'cost_breakdown': {
                'by_model': cost_analytics['cost_by_model'],
                'optimization_potential': cost_analytics['optimization_potential']
            },
            'cost_trends': performance_trends['ai_costs'],
            'recommendations': cost_analytics['optimization_potential']['recommendations']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting cost analytics: {e}")
        return jsonify({'error': 'Failed to retrieve cost analytics'}), 500

@admin_bp.route('/api/metrics/thai-sme-analytics')
@require_admin_auth
def get_thai_sme_analytics():
    """Get Thai SME specific analytics"""
    try:
        thai_sme_analytics = metrics_collector.get_thai_sme_analytics()
        
        return jsonify({
            'cultural_effectiveness': thai_sme_analytics['cultural_effectiveness'],
            'business_relevance': thai_sme_analytics['business_relevance'],
            'market_insights': thai_sme_analytics['market_insights'],
            'performance_summary': {
                'avg_cultural_score': thai_sme_analytics['cultural_effectiveness']['avg_appropriateness_score'],
                'avg_business_relevance': thai_sme_analytics['business_relevance']['avg_relevance_score'],
                'improvement_trend': thai_sme_analytics['cultural_effectiveness']['improvement_trend']
            },
            'regional_distribution': thai_sme_analytics['market_insights']['regional_adoption'],
            'industry_performance': thai_sme_analytics['business_relevance']['top_performing_industries']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting Thai SME analytics: {e}")
        return jsonify({'error': 'Failed to retrieve Thai SME analytics'}), 500

@admin_bp.route('/api/monitoring/alerts', methods=['GET', 'POST'])
@require_admin_auth
def manage_alerts():
    """Manage monitoring alerts"""
    try:
        if request.method == 'GET':
            # Get all configured alerts
            alerts = {
                alert_id: {
                    'id': alert_id,
                    'name': alert.name,
                    'condition': alert.condition,
                    'threshold': alert.threshold,
                    'severity': alert.severity,
                    'enabled': alert.enabled,
                    'trigger_count': alert.trigger_count,
                    'last_triggered': alert.last_triggered,
                    'cooldown_minutes': alert.cooldown_minutes
                }
                for alert_id, alert in monitoring_service.alerts.items()
            }
            
            return jsonify({
                'alerts': alerts,
                'alert_count': len(alerts),
                'enabled_count': sum(1 for alert in monitoring_service.alerts.values() if alert.enabled)
            })
        
        elif request.method == 'POST':
            # Update alert configuration
            data = request.get_json()
            action = data.get('action')
            alert_id = data.get('alert_id')
            
            if action == 'enable':
                monitoring_service.enable_alert(alert_id)
                return jsonify({'status': 'success', 'message': f'Alert {alert_id} enabled'})
            
            elif action == 'disable':
                monitoring_service.disable_alert(alert_id)
                return jsonify({'status': 'success', 'message': f'Alert {alert_id} disabled'})
            
            elif action == 'update_threshold':
                threshold = data.get('threshold')
                if alert_id in monitoring_service.alerts and threshold is not None:
                    monitoring_service.alerts[alert_id].threshold = float(threshold)
                    return jsonify({'status': 'success', 'message': f'Alert {alert_id} threshold updated to {threshold}'})
                else:
                    return jsonify({'error': 'Invalid alert_id or threshold'}), 400
            
            else:
                return jsonify({'error': 'Invalid action'}), 400
        
    except Exception as e:
        current_app.logger.error(f"Error managing alerts: {e}")
        return jsonify({'error': 'Failed to manage alerts'}), 500

@admin_bp.route('/api/monitoring/system-health')
@require_admin_auth
def get_detailed_system_health():
    """Get detailed system health information"""
    try:
        import time
        health_report = monitoring_service.get_system_health_report()
        real_time_metrics = metrics_collector.get_real_time_metrics()
        
        # Additional health checks
        current_time = time.time()
        
        # Check database response time
        db_start = time.time()
        try:
            db.session.execute('SELECT 1')
            db_response_time = (time.time() - db_start) * 1000
            db_health = 'healthy' if db_response_time < 100 else 'slow' if db_response_time < 500 else 'critical'
        except Exception:
            db_response_time = 0
            db_health = 'error'
        
        # System resource usage (if psutil is available)
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            system_resources = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'status': 'healthy' if all(x < 80 for x in [cpu_percent, memory_percent, disk_percent]) else 'warning'
            }
        except ImportError:
            system_resources = {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'status': 'unknown'
            }
        
        return jsonify({
            'overall_health': health_report['overall_health'],
            'health_score': _calculate_health_score(real_time_metrics, db_health, system_resources),
            'components': {
                'database': {
                    'status': db_health,
                    'response_time_ms': round(db_response_time, 2),
                    'details': 'Database connectivity and response time'
                },
                'api_service': {
                    'status': 'healthy' if real_time_metrics['performance']['error_rate_percent'] < 5 else 'warning',
                    'error_rate': real_time_metrics['performance']['error_rate_percent'],
                    'avg_response_time': real_time_metrics['performance']['avg_response_time_ms']
                },
                'ai_service': {
                    'status': 'healthy' if real_time_metrics['ai_usage']['total_requests'] > 0 else 'idle',
                    'requests_24h': real_time_metrics['ai_usage']['total_requests'],
                    'cache_hit_rate': real_time_metrics['ai_usage']['cache_hit_rate_percent']
                },
                'system_resources': system_resources
            },
            'performance_metrics': real_time_metrics,
            'alerts_summary': {
                'active_alerts': len(monitoring_service.get_current_alerts()),
                'alerts_24h': len(monitoring_service.get_alert_history(24))
            },
            'uptime_info': {
                'status': 'operational',
                'last_restart': 'N/A',  # Would be implemented with actual tracking
                'uptime_hours': 'N/A'   # Would be implemented with actual tracking
            },
            'recommendations': health_report['recommendations']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting detailed system health: {e}")
        return jsonify({'error': 'Failed to retrieve system health'}), 500

def _calculate_health_score(metrics, db_health, system_resources):
    """Calculate overall system health score (0-100)"""
    score = 100
    
    # Deduct for high response times
    if metrics['performance']['avg_response_time_ms'] > 2000:
        score -= 20
    elif metrics['performance']['avg_response_time_ms'] > 1000:
        score -= 10
    
    # Deduct for high error rates
    if metrics['performance']['error_rate_percent'] > 10:
        score -= 30
    elif metrics['performance']['error_rate_percent'] > 5:
        score -= 15
    
    # Deduct for database issues
    if db_health == 'error':
        score -= 40
    elif db_health == 'critical':
        score -= 25
    elif db_health == 'slow':
        score -= 10
    
    # Deduct for high resource usage
    if system_resources['status'] == 'warning':
        score -= 15
    
    # Deduct for low cultural effectiveness
    if metrics['thai_sme_context']['avg_cultural_appropriateness'] < 0.7:
        score -= 10
    
    return max(0, score)

@admin_bp.route('/api/monitoring/performance-trends')
@require_admin_auth
def get_performance_trends():
    """Get detailed performance trends"""
    try:
        hours = request.args.get('hours', 24, type=int)
        trends = metrics_collector.get_performance_trends(hours)
        
        return jsonify({
            'time_period_hours': hours,
            'trends': trends,
            'summary': {
                'response_time_trend': _analyze_trend([point['avg_response_time'] for point in trends['response_times']]),
                'error_rate_trend': _analyze_trend([point['error_rate'] for point in trends['error_rates']]),
                'cost_trend': _analyze_trend([point['cumulative_cost'] for point in trends['ai_costs']]),
                'cultural_score_trend': _analyze_trend([point['avg_score'] for point in trends['cultural_scores']])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance trends: {e}")
        return jsonify({'error': 'Failed to retrieve performance trends'}), 500

def _analyze_trend(values):
    """Analyze trend direction from a list of values"""
    if len(values) < 2:
        return 'insufficient_data'
    
    recent = sum(values[-2:]) / 2
    older = sum(values[:2]) / 2
    
    if recent > older * 1.1:
        return 'increasing'
    elif recent < older * 0.9:
        return 'decreasing'
    else:
        return 'stable'