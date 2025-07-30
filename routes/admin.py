from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from models import Conversation, SystemLog, WebhookEvent
from services.conversation_manager import ConversationManager
from app import db

admin_bp = Blueprint('admin', __name__)
conversation_manager = ConversationManager()

@admin_bp.route('/')
def dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html')

@admin_bp.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        # Get date range
        days = request.args.get('days', 7, type=int)
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic stats
        total_conversations = Conversation.query.filter(
            Conversation.created_at >= since_date
        ).count()
        
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
                'avg_response_time': round(avg_response_time or 0, 2)
            },
            'message_types': dict(message_types),
            'languages': dict(languages),
            'file_types': dict(file_types),
            'daily_activity': [
                {'date': str(date), 'count': count}
                for date, count in daily_activity
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/conversations')
def get_conversations():
    """Get recent conversations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        conversations = Conversation.query.order_by(
            desc(Conversation.created_at)
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'conversations': [
                {
                    'id': conv.id,
                    'user_id': conv.user_id,
                    'user_name': conv.user_name,
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
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/logs')
def get_logs():
    """Get system logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
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
                    'message': log.message,
                    'user_id': log.user_id,
                    'error_details': log.error_details,
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
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/webhooks')
def get_webhooks():
    """Get webhook events"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
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
                    'user_id': webhook.user_id,
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
        return jsonify({'error': str(e)}), 500
