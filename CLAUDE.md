# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
python main.py
# or via uv
uv run python main.py
```

### Development Environment
- Uses `uv` for dependency management
- Python 3.11+ required
- Dependencies defined in `pyproject.toml`

### Database Operations
- Database auto-initializes on startup
- Uses SQLite by default (`instance/linebot.db`)
- PostgreSQL support via `DATABASE_URL` environment variable

## Code Architecture

### Application Structure
- **Entry Point**: `main.py` imports Flask app from `app.py`
- **Blueprint Architecture**: Modular routing with webhooks and admin separated
- **Database**: SQLAlchemy with declarative base, auto-creates tables on startup
- **Services Layer**: Business logic separated into service classes

### Key Components

#### Core Services (`services/`)
1. **LineService**: LINE Messaging API integration, signature verification, message sending
2. **OpenAIService**: Azure OpenAI API calls for text generation and image analysis
3. **FileProcessor**: Multi-format file content extraction (PDF, DOCX, XLSX, PPTX, code files)
4. **ConversationManager**: Conversation history and context storage management

#### Data Models (`models.py`)
- **Conversation**: User interactions, messages, responses with language detection
- **SystemLog**: Application logs and error tracking
- **WebhookEvent**: LINE webhook event monitoring and processing metrics

#### Routing (`routes/`)
- **webhook.py**: Processes LINE webhook events (messages, follows, postbacks)
- **admin.py**: Dashboard API endpoints for statistics and monitoring

### Multi-Language Support
- **Primary Language**: Thai (th) - optimized for Thai SME support
- **Supported Languages**: English, Japanese, Korean, Chinese, Spanish, French, German, Italian, Portuguese, Russian
- **Auto Language Detection**: Based on Unicode character ranges
- **SME Prompts System**: Thai-first business advisory prompts in `prompts/sme_prompts.py`

### File Processing Capabilities
- **Documents**: PDF, DOCX, TXT, MD
- **Spreadsheets**: XLSX, XLS, CSV  
- **Presentations**: PPTX, PPT
- **Code Files**: Python, JavaScript, HTML, CSS, Java, C++, C, PHP, Ruby, Go, Rust
- **Images**: JPG, PNG, GIF, WebP (with GPT-4 Vision analysis)
- **Size Limit**: 20MB per file

### Configuration Management
- Environment-based configuration via `config.py`
- Development mode with graceful fallbacks when Azure OpenAI not configured
- Required environment variables for production:
  - `LINE_CHANNEL_ACCESS_TOKEN`
  - `LINE_CHANNEL_SECRET` 
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`

### Data Flow Pattern
1. LINE webhook events → signature verification → event processing
2. File uploads → content extraction → AI processing
3. Context management → conversation history → response generation
4. Response delivery → data logging → metrics storage

### Thai SME Business Context
The application is specifically designed for Thai Small and Medium Enterprises (SMEs):
- References Thai government resources (OSMEP, SME One)
- Understands Thai regulations (PDPA, tax laws, licensing)
- Provides culturally appropriate business advice
- Uses colloquial, friendly Thai language
- Focuses on practical, actionable guidance

### Admin Interface
- Web-based dashboard for monitoring bot performance
- Real-time statistics and conversation tracking  
- Bootstrap-based responsive UI with dark theme
- Charts and analytics for usage patterns

### Error Handling
- Comprehensive logging with database storage
- Multi-language error messages
- Development-friendly responses when services unavailable
- Graceful degradation for missing configuration