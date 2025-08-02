# Thai SME LINE Bot - Deployment Ready

## Project Overview
A sophisticated LINE Official Account webhook bot that leverages Azure OpenAI's GPT-4.1-nano for advanced multilingual AI conversations, with a focus on intelligent error handling and user-friendly system interactions.

## Recent Changes (August 2, 2025)

### ✅ Radical Simplification PRD Created
1. **Replit-Optimized Architecture Planning**
   - Created `REPLIT_SIMPLIFIED_LINEBOT_PRD.md` for system simplification
   - Designed 5-file architecture specifically for Replit deployment
   - Defined migration strategy from 50+ files to 5 core files
   - Established <1.5s response time targets for Replit environment

### ✅ Previous Deployment Fixes Applied (August 1, 2025)
1. **Enhanced PostgreSQL Configuration**
   - Optimized connection pool settings (10 connections, 5-minute recycle)
   - Added SSL configuration with proper fallback handling
   - Implemented TCP keepalive settings for connection stability
   - Added statement and idle transaction timeouts

2. **Database Retry Logic**
   - Created `utils/database.py` with comprehensive retry mechanisms
   - Exponential backoff for connection failures  
   - Automatic connection recovery and health monitoring
   - Flask context-aware database operations

3. **Health Check Enhancements**
   - Enhanced `/health` endpoint with database connectivity verification
   - Real-time PostgreSQL connection monitoring
   - Comprehensive system metrics (queue, circuit breaker, rate limiting)
   - Response time tracking and database version reporting

4. **Flask Application Context Management**
   - Created `utils/flask_context.py` for proper context handling
   - Fixed async worker thread context issues
   - Safe database operations outside request context
   - Proper error handling for context-dependent operations

5. **Message Queue Improvements**
   - Enhanced worker threads with Flask app context
   - Added timeout handling for long-running tasks
   - Improved error recovery and retry logic
   - Context-safe async message processing

## Key Technologies
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with connection pooling and retry logic
- **AI Integration**: Azure OpenAI (GPT-4.1-nano)
- **Messaging**: LINE Bot SDK with webhook architecture
- **Deployment**: Gunicorn WSGI server
- **Monitoring**: Health checks, metrics collection, circuit breakers

## Application Architecture

### Database Layer
- PostgreSQL with optimized connection pooling
- Connection retry logic with exponential backoff
- Health monitoring and automatic recovery
- Context-aware operations for async processing

### API Layer
- LINE Webhook endpoint with signature verification
- Admin dashboard with secure authentication
- Health check endpoint for deployment monitoring
- Comprehensive error handling and logging

### Processing Layer
- Async message queue with worker threads
- Flask context management for database operations
- Circuit breaker pattern for external API calls
- Rate limiting and cost optimization

## Health Check Status
```json
{
  "status": "healthy",
  "database": {
    "status": "healthy",
    "response_time_ms": 83.49,
    "database_type": "PostgreSQL",
    "version": "PostgreSQL 16.9",
    "active_connections": 2
  },
  "service": "LINE Bot Webhook - Ultra-Optimized with Fast Path"
}
```

## Deployment Readiness
- ✅ Database connection stability with retry logic
- ✅ Health check endpoint responds quickly (< 100ms)
- ✅ Flask application context properly managed
- ✅ Root endpoint redirects correctly
- ✅ Admin interface accessible and secure
- ✅ Comprehensive error handling and logging
- ✅ Connection pooling optimized for production

## Environment Variables Required
- `DATABASE_URL`: PostgreSQL connection string
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot API token
- `LINE_CHANNEL_SECRET`: LINE Bot webhook secret
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `SESSION_SECRET`: Flask session encryption key
- `ADMIN_USERNAME`: Admin interface username
- `ADMIN_PASSWORD_HASH`: Admin interface password hash

## User Preferences
- Language: English
- Focus: Production deployment readiness
- Communication style: Technical but clear
- Error handling: Comprehensive with fallbacks
- Documentation: Detailed architectural decisions

## Architecture Decisions Log
- **August 2, 2025**: Created radical simplification PRD for Replit-optimized deployment
- **August 2, 2025**: Designed 5-file architecture targeting <1.5s response times
- **August 1, 2025**: Enhanced database configuration for deployment stability
- **August 1, 2025**: Implemented comprehensive retry logic with exponential backoff
- **August 1, 2025**: Added Flask context management for async operations
- **August 1, 2025**: Enhanced health check endpoint with database monitoring
- **August 1, 2025**: Optimized connection pooling for production workloads