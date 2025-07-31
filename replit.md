# replit.md

## Overview

This is a LINE Official Account Bot integrated with Azure OpenAI that provides conversational AI capabilities. The bot can process text messages, images, and various file formats (documents, spreadsheets, presentations, code files) and respond using GPT-4. It includes an admin dashboard for monitoring conversations, webhook events, and system logs.

## Current Status (July 31, 2025)

**Application Status**: ✅ Running successfully on port 5000  
**Database**: ✅ PostgreSQL connected and operational  
**Services**: ✅ All core services initialized (AI, messaging, file processing)  
**Admin Interface**: ✅ Templates created and accessible  
**LINE Webhook**: ⚠️ Partially functional - needs LINE Official Account configuration

## Recent Changes (July 31, 2025)

- ✅ Fixed database connection issues with PostgreSQL configuration
- ✅ Resolved SQLAlchemy event listener errors during startup
- ✅ Fixed circular import issues with encryption services
- ✅ Created missing admin_login.html template
- ✅ Added application context checks for database operations
- ✅ Implemented signature verification bypass for development/testing
- ✅ Fixed various syntax errors and import issues
- ⚠️ Temporarily disabled encryption to resolve startup errors (needs re-implementation)

## Deployment Requirements

To make the LINE bot fully functional:
1. **Deploy to a public URL** using Replit's deployment feature
2. **Configure LINE Webhook**: Set webhook URL to `https://your-deployed-url.replit.app/webhook`
3. **Verify API Keys**: Ensure LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET are correct
4. **Test LINE Integration**: Send messages to your LINE Official Account

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Lightweight Python web framework chosen for its simplicity and flexibility
- **SQLAlchemy**: ORM for database operations with declarative base model
- **Blueprint Architecture**: Modular routing with separate blueprints for webhook and admin functionality

### Database Design
- **SQLite/PostgreSQL**: Uses SQLite for development with PostgreSQL support via environment configuration
- **Three Main Tables**:
  - `Conversation`: Stores user interactions, messages, and bot responses
  - `SystemLog`: Tracks application logs and errors
  - `WebhookEvent`: Monitors LINE webhook events and processing metrics

### External Service Integrations
- **LINE Messaging API**: Handles webhook events, message verification, and response sending
- **Azure OpenAI**: Provides GPT-4.1-nano optimized for speed and performance with vision capabilities
- **File Processing**: Supports PDF, DOCX, XLSX, PPTX, code files, and images

## Key Components

### Core Services
1. **LineService**: Manages LINE API interactions, signature verification, and message sending
2. **OpenAIService**: Handles Azure OpenAI API calls for text generation and image analysis
3. **FileProcessor**: Extracts text content from various file formats
4. **ConversationManager**: Manages conversation history and context storage

### Routing Structure
- **Webhook Route** (`/webhook`): Processes LINE webhook events (messages, follows, postbacks)
- **Admin Routes**: Dashboard API endpoints for statistics, conversations, and monitoring

### File Processing Capabilities
- **Documents**: PDF, DOCX, TXT, MD
- **Spreadsheets**: XLSX, XLS, CSV
- **Presentations**: PPTX, PPT
- **Code Files**: Multiple programming languages
- **Images**: JPG, PNG, GIF, WebP (with GPT-4 Vision analysis)

## Data Flow

1. **Incoming Messages**: LINE sends webhook events to `/webhook` endpoint
2. **Signature Verification**: Validates request authenticity using LINE channel secret
3. **Event Processing**: Routes different message types to appropriate handlers
4. **File Processing**: Extracts text content from uploaded files
5. **AI Processing**: Sends context and content to Azure OpenAI for response generation
6. **Response Delivery**: Sends generated response back through LINE API
7. **Data Storage**: Logs conversation, events, and system information to database

## External Dependencies

### Required Environment Variables
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE bot API access token
- `LINE_CHANNEL_SECRET`: LINE webhook signature verification
- `AZURE_OPENAI_API_KEY`: Azure OpenAI service key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)

### Python Libraries
- **LINE SDK**: `line-bot-sdk` for LINE API integration
- **OpenAI**: `openai` library for Azure OpenAI
- **File Processing**: `PyPDF2`, `openpyxl`, `python-docx`, `python-pptx`
- **Web Framework**: `Flask`, `Flask-SQLAlchemy`

## Deployment Strategy

### Configuration Management
- Environment-based configuration with fallback defaults
- Separate development and production settings
- Database URL configuration for different environments

### Application Structure
- **Entry Point**: `main.py` imports Flask app from `app.py`
- **Database Initialization**: Auto-creates tables on startup
- **Error Handling**: Comprehensive logging with database storage
- **Security**: Proxy fix middleware for deployment behind reverse proxies

### Admin Interface
- Web-based dashboard for monitoring bot performance
- Real-time statistics and conversation tracking
- Bootstrap-based responsive UI with dark theme
- Charts and analytics for usage patterns

### Language Support
- Multi-language error messages (English, Japanese)
- Language detection for user messages
- Configurable default language settings

The application is designed for cloud deployment with environment variable configuration, making it suitable for platforms like Heroku, Railway, or container-based deployments.