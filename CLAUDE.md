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

1. **LINE Webhook** → `/webhook` endpoint receives events (**SYNCHRONOUS - NEEDS ASYNC**)
2. **Signature Verification** → `LineService.verify_signature()` validates authenticity
3. **Event Routing** → Different message types (text/image/file) routed to specific handlers
4. **Context Building** → `ConversationManager` retrieves conversation history
5. **AI Processing** → `OpenAIService` generates responses using GPT-4 (**MONOLITHIC IN MAIN.PY**)
6. **Response Delivery** → `LineService.reply_message()` sends back to user
7. **Data Persistence** → Conversation logged to SQLAlchemy models (**NO ENCRYPTION**)

### Service Layer Dependencies

- **LineService** (`services/line_service.py`): Depends on LINE SDK, handles all LINE API interactions
- **OpenAIService** (`services/openai_service.py`): Depends on Azure OpenAI, manages AI model calls (**NEEDS EXTRACTION FROM MAIN.PY**)
- **FileProcessor** (`services/file_processor.py`): Depends on PyPDF2, openpyxl, python-docx, python-pptx (**NOT IMPLEMENTED**)
- **ConversationManager** (`services/conversation_manager.py`): Depends on SQLAlchemy models, manages context

### Critical Architecture Issues

1. **Monolithic main.py**: AI logic, webhook handlers, and business logic all mixed together
2. **Synchronous Processing**: Blocking webhook handlers cause timeouts and poor UX
3. **Missing Implementations**: File processing and Thai SME prompts not completed
4. **Security Vulnerabilities**: Database encryption removed, no PDPA compliance

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

**CURRENT IMPLEMENTATION GAPS:**
- `prompts/sme_prompts.py` needs comprehensive Thai business scenarios
- File processing implementation missing (`services/file_processor.py` incomplete)
- No business document analysis capabilities
- Generic AI responses lack Thai cultural context
- Missing SME-specific validation and business logic

### Performance & Security Trade-offs

**CRITICAL:** Recent encryption removal improved performance but created security vulnerabilities:
- Direct database writes without encryption (TEMPORARY SOLUTION)
- 30-second timeout handling with signal.SIGALRM
- Optimized OpenAI parameters: max_tokens=800, temperature=0.5
- Database indexes on frequently queried columns

**URGENT OPTIMIZATION NEEDS:**
- Async webhook processing to prevent blocking
- Field-level encryption for PDPA compliance
- Background task queue for heavy operations
- Service layer extraction from main.py monolith

## Critical Implementation Priorities

### Phase 1: Security & Performance (IMMEDIATE)
1. **Async Webhook Processing** - Convert main.py handlers to prevent blocking
2. **Restore Data Encryption** - Field-level encryption for PDPA compliance
3. **Extract AI Service** - Move OpenAI logic from main.py to dedicated service
4. **Background Tasks** - Queue system for file processing and heavy operations

### Phase 2: Thai SME Features (HIGH PRIORITY)
5. **Complete Thai Prompts** - Expand prompts/sme_prompts.py with business scenarios
6. **File Processing** - Implement services/file_processor.py for documents
7. **Cultural Validation** - Add Thai business context and etiquette checks
8. **SME Business Logic** - Industry-specific handlers and responses

### Phase 3: Infrastructure (MEDIUM PRIORITY)
9. **Database Optimization** - Query optimization and proper indexing
10. **Connection Pooling** - Reduce database connection overhead
11. **Performance Monitoring** - Real-time metrics and alerting
12. **PDPA Compliance** - Complete audit trail and user consent

## Critical Cursor Rules

From `.cursor/rules/coding-rules.mdc`:
- Always kill existing servers before starting new ones
- Look for existing code to iterate on instead of creating new code
- Avoid files over 200-300 lines - refactor at that point
- Never mock data for dev or prod environments
- Never overwrite .env file without confirmation
- Focus only on code relevant to the task

## Security & PDPA Compliance Requirements

### Critical Security Gaps
- **Data Encryption**: Removed for performance, MUST be restored with async implementation
- **Webhook Security**: Signature verification exists but needs rate limiting
- **Admin Access**: No authentication for admin endpoints
- **User Consent**: Missing PDPA consent collection and management
- **Data Retention**: No automated data deletion policy

### Thai PDPA Compliance Checklist
- [ ] User consent collection before data processing
- [ ] Privacy policy in Thai language
- [ ] Data retention and deletion mechanisms
- [ ] User rights implementation (access, rectification, erasure)
- [ ] Cross-border data transfer safeguards for Azure OpenAI

## File Processing Architecture

### Current Status
- **Dependencies Configured**: PyPDF2, openpyxl, python-docx, python-pptx in pyproject.toml
- **Implementation Missing**: services/file_processor.py needs complete implementation
- **Integration Gap**: No webhook handlers for file message types

### Required File Support
```python
# Thai SME document types to support:
Documents: PDF (reports, invoices), DOCX (contracts, proposals)
Spreadsheets: XLSX (financial statements, inventory)
Presentations: PPTX (business plans, pitches)
Images: JPG/PNG (receipts, documents) via GPT-4 Vision
```

### File Processing Pipeline Design
1. **Validation**: File size, type, malware scanning
2. **Extraction**: Format-specific content extraction with Thai text support
3. **AI Analysis**: Context-aware document understanding
4. **Response**: Structured insights for SME business decisions

## Error Handling Strategy

1. All webhook handlers wrapped in try/except blocks
2. Errors logged to SystemLog table with full stack traces
3. User-friendly error messages returned in multiple languages
4. Development mode provides detailed error feedback
5. Graceful degradation when external services unavailable

## LINE Bot Optimization Guidelines

### Webhook Response Time Requirements
- LINE platform requires response within 30 seconds
- Current synchronous processing often exceeds this limit
- Implement async processing with immediate acknowledgment
- Use background tasks for AI processing and file handling

### Message Type Processing Times
| Type | Current | Target | Solution |
|------|---------|--------|----------|
| Text | 3-8s | <2s | Async + caching |
| Image | 5-12s | <5s | Background OCR |
| File | 10-30s | <10s | Chunked processing |
| Postback | 1-3s | <1s | Direct routing |

## AI Service Optimization

### Azure OpenAI Configuration
```python
# Current (in main.py - needs extraction):
model="gpt-4"
max_tokens=800  # Static, should be dynamic
temperature=0.5  # Should vary by request type
```

### Recommended Optimizations
1. **Dynamic Token Allocation**: Adjust based on request complexity
2. **Response Caching**: Cache common Thai SME queries
3. **Prompt Templates**: Structured prompts for different business scenarios
4. **Context Compression**: Summarize old conversations to save tokens
5. **Streaming Responses**: Implement for better perceived performance

### Thai Language Considerations
- Preserve UTF-8 encoding throughout pipeline
- Implement Thai text normalization before AI processing
- Add cultural context injection for business appropriateness
- Consider regional dialects and business terminology

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.