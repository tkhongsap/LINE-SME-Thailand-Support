# Replit-Optimized LINE Bot PRD: Radical Simplification

## Executive Summary

### Project Objective
Transform the existing over-engineered Thai SME LINE Bot into a simple, fast, and maintainable system optimized for Replit's deployment environment.

### Problem Statement
Current system analysis reveals:
- **50+ files** overwhelming Replit's file explorer
- **Complex architecture** difficult to debug in Replit's console
- **185+ configuration parameters** scattered across multiple files
- **Multiple service layers** causing deployment complexity
- **Performance inconsistency** with response times up to 10.5s

### Solution: Replit-Native Simplification
Create a **5-file system** optimized for Replit's environment:
- Single-path message processing
- Direct Azure OpenAI integration 
- Simplified Flask deployment with Gunicorn
- Environment-based configuration only
- **Target: <1.5s response time**

## Replit Environment Considerations

### Replit-Specific Constraints
1. **File Management**: Replit works best with <20 core files
2. **Environment Variables**: Use Replit Secrets for all configuration
3. **Database**: PostgreSQL available via `DATABASE_URL`
4. **Deployment**: Gunicorn runs on port 5000 automatically
5. **Logging**: Console logs visible in Replit's workflow panel
6. **Health Checks**: Essential for Replit deployment monitoring

### Current Replit Setup Assessment
```
✅ PostgreSQL database connected (DATABASE_URL available)
✅ Gunicorn workflow configured for port 5000
✅ Environment secrets system ready
❌ Too many files (50+) causing navigation issues
❌ Complex service architecture hard to debug
❌ Multiple configuration systems creating conflicts
```

## Target Architecture for Replit

### Simplified File Structure
```
thai-sme-linebot/           # Root (5 core files only)
├── main.py                 # Gunicorn entry point (5 lines)
├── app.py                  # Flask app + routes (100 lines)
├── openai_service.py       # Direct Azure OpenAI (80 lines)
├── line_service.py         # LINE API wrapper (60 lines)
└── database.py             # Simple logging (40 lines)

# Keep existing (no changes needed)
├── replit.md              # Project documentation
├── pyproject.toml         # Dependencies
└── .env.example           # Template for secrets
```

### Replit-Optimized Data Flow
```
┌─────────────────────────────────────┐
│    Replit Deployment (Port 5000)    │
├─────────────────────────────────────┤
│         Gunicorn Server             │
├─────────────────────────────────────┤
│          Flask App                  │
│    /webhook (LINE messages)         │
│    /health (deployment check)       │
├─────────────────────────────────────┤
│      Direct Azure OpenAI           │
│         (800-1200ms)                │
├─────────────────────────────────────┤
│     PostgreSQL Logging             │
│      (async, non-blocking)          │
└─────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core Simplification (Week 1)

#### Day 1-2: Create New Files
```python
# main.py (Replit entry point)
from app import app

# app.py (All routes in one file)
from flask import Flask, request, abort
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Complete webhook logic here
    pass

@app.route('/health')
def health():
    # Replit deployment health check
    pass
```

#### Day 3-4: Integrate Services
- Direct Azure OpenAI calls (no intermediate services)
- Simple LINE API wrapper
- Async database logging

#### Day 5: Replit Deployment Testing
- Test Gunicorn startup on port 5000
- Verify environment variables from Replit Secrets
- Check PostgreSQL connectivity
- Validate webhook response times

### Phase 2: Migration Strategy

#### Replit-Specific Migration Steps
1. **Create new simplified files** alongside existing system
2. **Test in Replit console** using workflow logs
3. **Switch Gunicorn command** to new main.py
4. **Verify health endpoint** responds quickly
5. **Remove old files** after successful deployment

### Phase 3: Replit Optimization

#### Performance Targets for Replit
| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time (p95) | <1.5s | Workflow console logs |
| Memory Usage | <512MB | Replit system monitor |
| File Count | <10 core files | File explorer |
| Environment Variables | <10 secrets | Replit Secrets panel |

## Technical Specifications

### Replit Environment Configuration

#### Required Replit Secrets
```bash
# LINE Bot (from LINE Developer Console)
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here

# Azure OpenAI (from Azure Portal)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano

# Flask (generate random string)
SESSION_SECRET=your_random_secret_here

# Database (auto-provided by Replit)
DATABASE_URL=postgresql://... (auto-configured)
```

#### Simplified app.py Structure
```python
import os
import json
import logging
from flask import Flask, request, abort, jsonify
from openai_service import generate_response
from line_service import verify_signature, send_message
from database import log_conversation

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify LINE signature
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    if not verify_signature(body, signature):
        abort(400)
    
    # Process events
    events = json.loads(body).get('events', [])
    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            reply_token = event['replyToken']
            user_message = event['message']['text']
            user_id = event['source']['userId']
            
            # Generate response (direct OpenAI call)
            response = generate_response(user_message)
            
            # Send to LINE
            send_message(reply_token, response)
            
            # Log async (non-blocking)
            log_conversation(user_id, user_message, response)
    
    return 'OK', 200

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "deployment": "replit",
        "database": "postgresql",
        "version": "2.0-simplified"
    })

@app.route('/')
def root():
    return "Thai SME LINE Bot - Simplified for Replit", 200
```

### Database Schema (Minimal)
```sql
-- Simple conversation logging
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
```

## Replit Deployment Process

### Step 1: Prepare Replit Environment
1. **Set Replit Secrets** (6 environment variables)
2. **Verify PostgreSQL** connection via `DATABASE_URL`
3. **Test Gunicorn startup** on port 5000
4. **Check file permissions** and structure

### Step 2: Deploy Simplified System
1. **Create new simplified files** (5 files total)
2. **Update pyproject.toml** with minimal dependencies
3. **Test webhook locally** using Replit's console
4. **Switch main.py** to new entry point

### Step 3: Validation
1. **Health check responds** at `/health`
2. **Webhook processes** LINE messages correctly
3. **Response times** consistently <1.5s
4. **Database logging** works without blocking

### Step 4: Cleanup
1. **Remove old complex files** (routes/, services/, utils/)
2. **Keep only 5 core files** + configuration
3. **Update replit.md** with new architecture
4. **Document simplified deployment**

## Success Criteria

### Replit-Specific KPIs
| Metric | Target | How to Measure |
|--------|--------|----------------|
| File Count | <10 files | Replit file explorer |
| Response Time | <1.5s | Workflow console logs |
| Memory Usage | <512MB | Replit system monitor |
| Deployment Time | <30s | Gunicorn startup time |
| Debug Complexity | <5 min to trace issues | Console log clarity |

### User Experience KPIs  
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Message Success Rate | >99% | Database logs |
| Average Response Time | <1s | Application metrics |
| Error Rate | <1% | Exception tracking |
| Uptime | >99.9% | Replit deployment status |

## Risk Mitigation

### Replit-Specific Risks
1. **Port conflicts**: Ensure only port 5000 is used
2. **Environment variable issues**: Use Replit Secrets exclusively
3. **File permission errors**: Keep simple file structure
4. **Database connection limits**: Use connection pooling
5. **Memory constraints**: Monitor usage, keep <512MB

### Migration Risks
1. **Feature loss**: Document all current features, ensure coverage
2. **Performance regression**: Load test before full migration
3. **Environment issues**: Test all Replit Secrets integration
4. **Database compatibility**: Verify PostgreSQL schema works

## Implementation Timeline

### Week 1: Build & Test
- **Day 1-2**: Create 5 simplified files
- **Day 3**: Test in Replit environment  
- **Day 4**: Integrate Azure OpenAI + LINE APIs
- **Day 5**: Load testing and optimization

### Week 2: Deploy & Monitor
- **Day 1**: Deploy to Replit staging
- **Day 2-3**: Monitor performance and fix issues
- **Day 4**: Switch production traffic
- **Day 5**: Remove old files and cleanup

### Week 3: Optimize
- **Monitor** response times and error rates
- **Optimize** based on real Replit performance data
- **Document** lessons learned for future deployments

## Conclusion

This PRD transforms the complex LINE bot architecture into a Replit-native, simplified system that:

- **Reduces complexity** from 50+ files to 5 core files
- **Improves maintainability** with clear, single-purpose files
- **Optimizes for Replit** environment and deployment process
- **Delivers consistent performance** <1.5s response times
- **Simplifies debugging** through console log clarity

The result will be a production-ready system that leverages Replit's strengths while eliminating architectural complexity that doesn't serve user needs.