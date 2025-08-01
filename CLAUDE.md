# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies using uv package manager
uv sync

# Start development server
python main.py
# OR
python app.py

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
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4  # defaults to gpt-4
DATABASE_URL=sqlite:///linebot.db  # defaults to SQLite, use PostgreSQL URL for production
```

## Architecture Overview

This is a LINE Bot application designed for Thai SME (Small and Medium Enterprise) support, using Azure OpenAI for conversational AI capabilities.

### Request Flow Architecture

1. **LINE Webhook** → `/webhook` endpoint receives events
2. **Signature Verification** → `LineService.verify_signature()` validates authenticity
3. **Event Routing** → Different message types (text/image/file) routed to specific handlers
4. **Context Building** → `ConversationManager` retrieves conversation history
5. **AI Processing** → `OpenAIService` generates responses using GPT-4
6. **Response Delivery** → `LineService.reply_message()` sends back to user
7. **Data Persistence** → Conversation logged to SQLAlchemy models

### Service Layer Dependencies

- **LineService** (`services/line_service.py`): Depends on LINE SDK, handles all LINE API interactions
- **OpenAIService** (`services/openai_service.py`): Depends on Azure OpenAI, manages AI model calls
- **FileProcessor** (`services/file_processor.py`): Depends on PyPDF2, openpyxl, python-docx, python-pptx
- **ConversationManager** (`services/conversation_manager.py`): Depends on SQLAlchemy models, manages context

### Database Transaction Flow

All database operations flow through SQLAlchemy session management:
- Conversations are created/updated with each message
- SystemLogs capture errors with stack traces
- WebhookEvents track performance metrics
- Sessions are properly committed/rolled back in try/finally blocks

### Multi-language Architecture

The system uses a unified multilingual approach:
- AI automatically detects user language from messages
- Responds naturally in the detected language
- System prompts in `prompts/sme_prompts.py` guide language behavior
- No hardcoded language switching - AI handles it contextually

### Thai SME Business Logic

The core business logic centers around Thai SME support with specialized knowledge:
- Financial literacy and funding (SME loans, cash flow)
- Digital marketing and social commerce (LINE, Facebook, TikTok)
- E-commerce and online presence (marketplaces, payment gateways)
- Operations management (HR, inventory, customer service)
- Legal compliance (PDPA, tax laws, business registration)

### Performance Considerations

Recent optimization removed encryption layer that was causing 2+ minute response times:
- Direct database writes without encryption overhead
- 30-second timeout handling with signal.SIGALRM
- Optimized OpenAI parameters: max_tokens=800, temperature=0.5
- Database indexes on frequently queried columns

## Critical Cursor Rules

From `.cursor/rules/coding-rules.mdc`:
- Always kill existing servers before starting new ones
- Look for existing code to iterate on instead of creating new code
- Avoid files over 200-300 lines - refactor at that point
- Never mock data for dev or prod environments
- Never overwrite .env file without confirmation
- Focus only on code relevant to the task

## Error Handling Strategy

1. All webhook handlers wrapped in try/except blocks
2. Errors logged to SystemLog table with full stack traces
3. User-friendly error messages returned in multiple languages
4. Development mode provides detailed error feedback
5. Graceful degradation when external services unavailable
