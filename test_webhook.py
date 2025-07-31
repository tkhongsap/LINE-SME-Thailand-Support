#!/usr/bin/env python3
import requests
import json
import time
import hashlib
import hmac
import base64
import os

# Test webhook locally
WEBHOOK_URL = "http://localhost:5001/webhook"

# Create a test webhook event
test_event = {
    "events": [{
        "type": "message",
        "message": {
            "type": "text", 
            "id": "test123",
            "text": "สวัสดีครับ"
        },
        "timestamp": int(time.time() * 1000),
        "source": {
            "type": "user",
            "userId": "U0aa9b562d6edb7c42aac9668f2215349"
        },
        "replyToken": f"test-reply-token-{int(time.time())}"
    }]
}

# Convert to JSON
body = json.dumps(test_event)

# Create signature (for testing, we'll skip signature validation)
# Set debug mode to bypass signature validation
os.environ['WEBHOOK_DEBUG_MODE'] = 'true'

headers = {
    "Content-Type": "application/json",
    "X-Line-Signature": "test-signature"
}

print("Sending test webhook event...")
print(f"Body: {body}")

try:
    response = requests.post(WEBHOOK_URL, data=body, headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
except Exception as e:
    print(f"Error: {e}")