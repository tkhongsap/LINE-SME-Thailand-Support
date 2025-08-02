import os
import json
import logging
import time
import psutil
from flask import Flask, request, abort, jsonify
from openai_service import generate_response as openai_generate
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
                    logging.info(f"📨 Received message from {user_id}: {user_message}")
                    
                    # Measure OpenAI API latency separately
                    openai_start_time = time.time()
                    response_text = openai_generate(user_message)
                    openai_latency_ms = int((time.time() - openai_start_time) * 1000)
                    
                    logging.info(f"🤖 Generated response: {response_text[:50]}...")
                    
                    # Send response via LINE
                    send_message(reply_token, response_text)
                    
                    # Calculate total performance metrics
                    total_response_time_ms = int((time.time() - total_start_time) * 1000)
                    
                    # Memory usage monitoring for Replit constraints
                    memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    
                    # Performance monitoring log with validation
                    performance_status = "🟢 OPTIMAL" if total_response_time_ms < 1000 else "🟡 SLOW"
                    memory_status = "🟢 OK" if memory_usage_mb < 400 else "🟡 HIGH"
                    
                    logging.info(f"⚡ Performance: {performance_status} Total={total_response_time_ms}ms | OpenAI={openai_latency_ms}ms | Memory={memory_usage_mb:.1f}MB {memory_status}")
                    
                    # Log conversation to console (Replit-optimized)
                    logging.info(f"💬 {user_id[:10]}... | {total_response_time_ms}ms | {memory_usage_mb:.1f}MB | {user_message[:30]}... → {response_text[:30]}...")
        
        return 'OK', 200
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        # Never fail webhook - LINE requires 200 response
        return 'OK', 200

@app.route('/health')
def health():
    """Replit deployment health check endpoint"""
    try:
        # Basic health status
        health_data = {
            "status": "healthy",
            "deployment": "replit-simplified",
            "version": "2.1.0",
            "response_time_target": "500ms",
            "timestamp": int(__import__('time').time())
        }
        
        # Test environment variables
        required_env_vars = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 
                           'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'SESSION_SECRET']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            health_data["status"] = "degraded"
            health_data["missing_env_vars"] = missing_vars
        
        # Console-only logging - no database connectivity required
        health_data["storage"] = "console-only"
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "deployment": "replit-simplified"
        }), 500

@app.route('/')
def root():
    """Simple root endpoint with status message"""
    return jsonify({
        "service": "Thai SME LINE Bot - Simplified",
        "status": "running",
        "deployment": "replit",
        "version": "2.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }), 200

if __name__ == "__main__":
    # Development server (Gunicorn handles production)
    app.run(host="0.0.0.0", port=5000, debug=True)