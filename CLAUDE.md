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

# Kill existing servers before starting new ones (as per Cursor rules)
pkill -f gunicorn
```

## Required Environment Variables

```bash
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-nano  # defaults to gpt-4.1-nano
DATABASE_URL=postgresql://...  # PostgreSQL connection string
SESSION_SECRET=your_session_secret
ADMIN_USERNAME=admin_username
ADMIN_PASSWORD_HASH=hashed_password
```

## Architecture Overview

This is a radically simplified LINE Bot application (v2.0) optimized for Replit deployment. The system was transformed from a complex 50+ file architecture to just 5 core files.

### Core Files (Total: ~519 lines)

1. **main.py** - Gunicorn entry point that imports app_simplified
2. **app_simplified.py** - Flask application with webhook handler and all routes
3. **openai_service.py** - Direct Azure OpenAI integration without abstraction layers
4. **line_service.py** - Minimal LINE API wrapper for signature verification and messaging
5. **database.py** - Async PostgreSQL logging with connection pooling

### Request Flow

```
LINE Webhook → Signature Verification → OpenAI Processing → Response → Async Log
    (10ms)            (5ms)               (800-1200ms)      (100ms)   (non-blocking)
```

### Key Design Decisions

- **Single processing path** - No complex fast path/full pipeline routing
- **Direct API calls** - Removed all service abstraction layers
- **Async database logging** - Uses threading to prevent blocking main flow
- **Connection pooling** - 1-5 connections optimized for Replit constraints
- **5-second timeout** - OpenAI calls timeout to maintain responsiveness

## Critical Cursor Rules

From `.cursor/rules/coding-rules.mdc`:
- Always kill existing servers before starting new ones
- Look for existing code to iterate on instead of creating new code
- Avoid files over 200-300 lines - refactor at that point
- Never mock data for dev or prod environments
- Never overwrite .env file without confirmation
- Focus only on code relevant to the task

## Performance Targets

- Health endpoint: <500ms
- Root endpoint: <100ms
- Message response: <1.5s (p95)
- Memory usage: <512MB (Replit constraint)
- Database connections: 1-5 max

## Error Handling Strategy

- All webhook errors return 200 OK to prevent LINE retries
- User-friendly error messages in Thai/English based on detected language
- Comprehensive logging without exposing sensitive data
- Graceful degradation when services unavailable

## Business Context

Thai SME (Small and Medium Enterprise) support bot with specialized knowledge in:
- Financial literacy and funding options
- Digital marketing and social commerce
- E-commerce and online presence
- Operations management
- Legal compliance (PDPA, tax laws)

The bot automatically detects language from user messages and responds in the same language (Thai/English).

## Important Notes

- The `/backup/` directory contains the old complex architecture (50+ files) - DO NOT USE
- Database schema is auto-created on first run
- All configuration via environment variables only
- Deployment verified through DEPLOYMENT_CHECKLIST.md
- Performance validated to meet all targets in August 2025 deployment