import os
import json
import logging
import time
from flask import Flask, request, abort, jsonify
from openai_service import generate_response as openai_generate
from line_service import verify_signature, send_message
from database import log_conversation, get_database_service

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
                    start_time = time.time()
                    logging.info(f"Received message from {user_id}: {user_message}")
                    
                    # Generate response using OpenAI
                    response_text = openai_generate(user_message, 'th')
                    logging.info(f"Generated response: {response_text[:50]}...")
                    
                    # Send response via LINE
                    send_message(reply_token, response_text)
                    
                    # Log conversation async (non-blocking)
                    response_time_ms = int((time.time() - start_time) * 1000)
                    log_conversation(user_id, user_message, response_text, response_time_ms)
        
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
            "version": "2.0.0",
            "response_time_target": "1.5s",
            "timestamp": int(__import__('time').time())
        }
        
        # Test environment variables
        required_env_vars = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 
                           'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'DATABASE_URL']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            health_data["status"] = "degraded"
            health_data["missing_env_vars"] = missing_vars
        
        # Test database connectivity
        try:
            db_service = get_database_service()
            db_healthy = db_service.health_check()
            health_data["database"] = "healthy" if db_healthy else "unhealthy"
        except Exception as e:
            health_data["database"] = "unhealthy"
            health_data["database_error"] = str(e)
        
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