# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies using uv package manager
uv sync

# Start development server
python main.py

# Start production server (Replit deployment)
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Kill existing servers before starting new ones (IMPORTANT: Cursor rule)
pkill -f gunicorn
pkill -f python

# Database operations
sqlite3 instance/linebot.db  # Access SQLite database
```

## Required Environment Variables

```bash
# LINE Bot Configuration (REQUIRED)
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Azure OpenAI Configuration (REQUIRED)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-nano  # Critical: Must use gpt-4.1-nano, not gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-02-01

# Optional Configuration
DATABASE_URL=sqlite:///instance/linebot.db  # PostgreSQL URL for production
SESSION_SECRET=your-session-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=sha256_hash_of_password
```

## Architecture Overview

LINE Bot application for Thai SME support using Azure OpenAI GPT-4.1-nano for conversational AI.

### Critical Architecture Decisions

1. **No Encryption Layer**: Removed due to 2+ minute response time bottleneck
2. **Async Processing**: Message queue with ThreadPoolExecutor for webhook responses
3. **Development Mode Fallback**: Graceful degradation when Azure OpenAI unavailable
4. **Flask App Context**: Required in all async handlers for database access

### Request Processing Flow

```
LINE Webhook → Signature Verification → Event Router → Message Queue
                                                           ↓
Response ← LINE API ← Response Generator ← OpenAI API ← Task Handler
   ↓
Database (Conversation, SystemLog, WebhookEvent)
```

### Service Layer Architecture

**Core Services** (all in `services/` directory):
- **LineService/OptimizedLineService**: LINE API wrapper with connection pooling
- **OpenAIService**: Azure OpenAI integration with retry logic and optimization
- **FileProcessor/StreamingFileProcessor**: Multi-format file content extraction
- **ConversationManager**: Context management with language detection
- **MessageQueue**: Async task processing for webhook responses
- **AIOptimizer**: Response caching, token optimization, model selection
- **SMEIntelligence**: Thai business context and cultural awareness

### Complex Service Dependencies

1. **Webhook Processing** (`routes/webhook.py`):
   - Uses WebhookProcessor for batch processing
   - Registers queue handlers with Flask app context
   - Implements circuit breaker pattern for LINE API
   - Rate limiting per user and API level

2. **AI Response Generation**:
   - SMEPrompts → Dynamic prompt injection based on business context
   - AIOptimizer → Caches responses, selects models, compresses context
   - MetricsCollector → Tracks performance, costs, cultural effectiveness

3. **Database Session Management**:
   - All async handlers must use `with app.app_context()`
   - Bulk operations use `db.session.bulk_save_objects()`
   - Proper rollback in exception handlers

### Thai SME Business Intelligence

**Industry Contexts** (in `SMEPrompts.INDUSTRY_CONTEXTS`):
- retail, manufacturing, food, agriculture, services, technology

**Business Stages** (in `SMEPrompts.STAGE_CONTEXTS`):
- startup, growth, established, pivot

**Cultural Intelligence**:
- Buddhist values integration
- Thai business hierarchy respect
- Regional variations (Bangkok vs provincial)
- Formality levels (polite, formal, casual)

### Performance Optimizations

1. **Database Indexes** (composite indexes on):
   - user_id + created_at
   - language + created_at
   - message_type + created_at

2. **Response Time Targets**:
   - Webhook acknowledgment: < 1 second
   - Text response: < 3 seconds
   - File processing: < 30 seconds

3. **Caching Strategy**:
   - Response cache with semantic matching
   - User language preferences
   - Flex message templates

## Critical Cursor Coding Rules

From `.cursor/rules/coding-rules.mdc`:
- **ALWAYS** kill existing servers before starting new ones
- **ALWAYS** look for existing code before creating new code
- **NEVER** mock data for dev or prod environments
- **NEVER** overwrite .env file without confirmation
- **AVOID** files over 200-300 lines (refactor instead)
- **AVOID** changing existing patterns without exhausting current implementation

## Known Issues and Workarounds

1. **Flask App Context in Async Handlers**:
   ```python
   from app import app
   with app.app_context():
       # Database operations here
   ```

2. **Azure OpenAI Model Name**:
   - Must use `gpt-4.1-nano` (not `gpt-35-turbo`)
   - Fallback to dev responses if API fails

3. **Signal Handling for Timeouts**:
   - Only works in main thread
   - Use ThreadPoolExecutor for async processing

4. **Replit Deployment**:
   - Uses port 5000 internally, mapped to 80 externally
   - Requires `--reuse-port` flag for gunicorn

## Testing and Debugging

```bash
# Test webhook locally
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"events":[]}'

# Check database
sqlite3 instance/linebot.db "SELECT COUNT(*) FROM conversations;"

# View logs
sqlite3 instance/linebot.db "SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 10;"

# Generate admin password hash
python -c "import hashlib; print(hashlib.sha256('your_password'.encode()).hexdigest())"
```

## Admin Dashboard Access

1. Navigate to `/admin`
2. Login with configured credentials
3. Monitor endpoints:
   - `/api/stats` - Dashboard statistics
   - `/api/conversations` - Recent conversations
   - `/api/optimization-metrics` - AI performance
   - `/api/async-processing-metrics` - Queue status