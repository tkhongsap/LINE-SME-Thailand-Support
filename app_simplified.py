import os
import json
import logging
import time
import psutil
from flask import Flask, request, abort, jsonify
from openai_service import (
    generate_response as openai_generate,
    get_conversation_history,
    update_conversation_history,
    cleanup_expired_sessions,
    get_session_stats
)
from line_service import verify_signature, send_message


# Configure logging for Replit console visibility
logging.basicConfig(level=logging.INFO)

# Create simplified Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-replit")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Simplified webhook handler for LINE messages"""
    try:
        # Get signature and body for verification
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)
        
        if not signature or not body:
            abort(400)
        
        # Verify LINE signature
        if not verify_signature(body, signature):
            logging.error("Invalid LINE signature")
            abort(400)
        
        # Parse LINE webhook events
        try:
            events_data = json.loads(body)
            events = events_data.get('events', [])
        except json.JSONDecodeError:
            logging.error("Invalid JSON in webhook body")
            abort(400)
        
        # Process each event
        for event in events:
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                reply_token = event.get('replyToken')
                user_message = event.get('message', {}).get('text')
                user_id = event.get('source', {}).get('userId')
                
                if reply_token and user_message and user_id:
                    total_start_time = time.time()
                    logging.info(f"📨 Received message from {user_id[:10]}...: {user_message[:50]}...")
                    
                    try:
                        # Get conversation history for context
                        conversation_history = get_conversation_history(user_id)
                        history_length = len(conversation_history)
                        
                        # Measure OpenAI API latency separately
                        openai_start_time = time.time()
                        response_text = openai_generate(user_message, conversation_history)
                        openai_latency_ms = int((time.time() - openai_start_time) * 1000)
                        
                        logging.info(f"🤖 Generated response: {response_text[:50]}... (context: {history_length} msgs)")
                        
                        # Update conversation history with the exchange
                        update_conversation_history(user_id, user_message, response_text)
                        
                        # Send response via LINE
                        send_message(reply_token, response_text)
                        
                        # Calculate total performance metrics
                        total_response_time_ms = int((time.time() - total_start_time) * 1000)
                        
                        # Memory usage monitoring for Replit constraints
                        memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
                        
                        # Get session statistics for enhanced monitoring
                        session_stats = get_session_stats()
                        
                        # Performance monitoring log with validation
                        performance_status = "🟢 OPTIMAL" if total_response_time_ms < 3000 else "🟡 SLOW"
                        memory_status = "🟢 OK" if memory_usage_mb < 400 else "🟡 HIGH"
                        
                        logging.info(f"⚡ Performance: {performance_status} Total={total_response_time_ms}ms | OpenAI={openai_latency_ms}ms | Memory={memory_usage_mb:.1f}MB {memory_status}")
                        logging.info(f"💾 Sessions: {session_stats['active_sessions']} active | {session_stats['total_messages']} total msgs | {session_stats['memory_estimate_mb']:.1f}MB conversation data")
                        
                        # Enhanced conversation log with context indicators
                        context_indicator = f"[Ctx:{history_length}]" if history_length > 0 else "[New]"
                        logging.info(f"💬 {user_id[:10]}... {context_indicator} | {total_response_time_ms}ms | {memory_usage_mb:.1f}MB | {user_message[:30]}... → {response_text[:30]}...")
                        
                        # Periodic cleanup of expired sessions
                        if total_response_time_ms % 10 == 0:  # Every ~10th request
                            cleanup_expired_sessions()
                            
                    except Exception as session_error:
                        logging.error(f"Session management error: {session_error}")
                        # Fallback to basic response without session management
                        response_text = openai_generate(user_message)
                        send_message(reply_token, response_text)
                        logging.info("Fallback response sent without session management")
        
        return 'OK', 200
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        # Never fail webhook - LINE requires 200 response
        return 'OK', 200

@app.route('/health')
def health():
    """Enhanced Replit deployment health check endpoint with session monitoring"""
    try:
        # Get session statistics for monitoring
        session_stats = get_session_stats()
        memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Basic health status
        health_data = {
            "status": "healthy",
            "deployment": "replit-enhanced",
            "version": "2.2.0",
            "response_time_target": "3000ms",
            "timestamp": int(__import__('time').time()),
            "features": [
                "alex_hormozi_persona",
                "conversation_memory",
                "multilingual_detection",
                "thai_cultural_adaptation"
            ]
        }
        
        # Enhanced session monitoring
        health_data["session_management"] = {
            "active_sessions": session_stats['active_sessions'],
            "total_messages": session_stats['total_messages'],
            "memory_estimate_mb": round(session_stats['memory_estimate_mb'], 2),
            "memory_status": "OK" if session_stats['memory_estimate_mb'] < 50 else "HIGH"
        }
        
        # Performance monitoring
        health_data["performance"] = {
            "system_memory_mb": round(memory_usage_mb, 1),
            "memory_status": "OK" if memory_usage_mb < 400 else "HIGH",
            "conversation_storage": "in-memory",
            "session_timeout": "1 hour"
        }
        
        # Test environment variables
        required_env_vars = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 
                           'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'SESSION_SECRET']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            health_data["status"] = "degraded"
            health_data["missing_env_vars"] = missing_vars
        
        # Storage architecture update
        health_data["storage"] = "in-memory-sessions"
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "deployment": "replit-enhanced"
        }), 500

@app.route('/')
def root():
    """Simple root endpoint with status message"""
    return jsonify({
        "service": "Thai SME LINE Bot - Simplified",
        "status": "running",
        "deployment": "replit",
        "version": "2.1.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }), 200

if __name__ == "__main__":
    # Development server (Gunicorn handles production)
    app.run(host="0.0.0.0", port=5000, debug=True)