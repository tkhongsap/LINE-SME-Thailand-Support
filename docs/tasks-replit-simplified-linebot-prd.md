# Tasks: Replit Simplified LINE Bot Implementation

Based on `REPLIT_SIMPLIFIED_LINEBOT_PRD.md` - transforming the current 50+ file complex architecture into a 5-file Replit-optimized system.

## Current State Assessment

**Existing Infrastructure:**
- Complex architecture with 50+ files across multiple directories
- Current Flask app (`app.py`, `main.py`) with advanced features
- Multiple service layers (`services/`, `routes/`, `utils/`)
- PostgreSQL database already configured via `DATABASE_URL`
- Gunicorn workflow set up for port 5000
- Azure OpenAI integration exists but complex

**Target Architecture:**
- 5 core files: `main.py`, `app.py`, `openai_service.py`, `line_service.py`, `database.py`
- Direct API integrations without intermediate layers
- <1.5s response time target
- Replit-native deployment optimization

## Relevant Files

- `main.py` - New simplified Gunicorn entry point (will replace existing)
- `app.py` - New consolidated Flask application with all routes (will replace existing)
- `openai_service.py` - Direct Azure OpenAI integration service (new, replaces services/openai_service.py)
- `line_service.py` - Simple LINE API wrapper (new, replaces services/line_service.py)
- `database.py` - Minimal async logging service (new, replaces utils/database.py)
- `pyproject.toml` - Updated with minimal dependencies (will modify existing)
- `replit.md` - Updated documentation (will modify existing)

### Notes

- Will create new simplified files alongside existing complex architecture
- Migration will involve gradual transition and cleanup of old files
- Focus on Replit environment constraints (memory <512MB, file count <10)
- All configuration via Replit Secrets (environment variables only)

## Tasks

- [ ] 1.0 Create Simplified Core Architecture
  - [x] 1.1 Create new simplified `main.py` with 5 lines (Gunicorn entry point)
  - [x] 1.2 Create new consolidated `app.py` with Flask app, webhook route, health route (target: 100 lines)
  - [x] 1.3 Set up Flask app configuration for Replit environment (port 5000, session secret)
  - [x] 1.4 Implement signature verification and basic error handling in webhook
  - [x] 1.5 Create `/health` endpoint optimized for Replit deployment monitoring
  - [x] 1.6 Add root route `/` with simple status message

- [x] 2.0 Implement Direct API Integrations
  - [x] 2.1 Create `openai_service.py` with direct Azure OpenAI client initialization
  - [x] 2.2 Implement `generate_response()` function with simple prompt template
  - [x] 2.3 Add OpenAI error handling and timeout configuration (5 seconds)
  - [x] 2.4 Create `line_service.py` with LINE API wrapper functions
  - [x] 2.5 Implement `verify_signature()`, `send_message()`, and `send_push_message()` functions
  - [x] 2.6 Add LINE API error handling and retry logic for token expiry
  - [x] 2.7 Configure services to use Replit Secrets for API keys

- [x] 3.0 Set Up Replit-Optimized Database Layer
  - [x] 3.1 Create simplified `database.py` with async logging functions (target: 40 lines)
  - [x] 3.2 Implement `log_conversation()` function for non-blocking database writes
  - [x] 3.3 Set up minimal database schema (conversations table only)
  - [x] 3.4 Configure PostgreSQL connection using Replit's `DATABASE_URL`
  - [x] 3.5 Add database connection pooling optimized for Replit constraints
  - [x] 3.6 Implement database health check for monitoring

- [ ] 4.0 Test and Validate Performance in Replit Environment
  - [x] 4.1 Test Gunicorn startup time (<30 seconds) in Replit workflow
  - [x] 4.2 Validate webhook endpoint responds to LINE messages
  - [x] 4.3 Test Azure OpenAI integration with actual API calls
  - [x] 4.4 Measure response times and ensure <1.5s target is met
  - [x] 4.5 Test database logging works without blocking main thread
  - [x] 4.6 Verify health endpoint returns proper status in <100ms
  - [x] 4.7 Load test with multiple concurrent requests to verify Replit performance
  - [x] 4.8 Test all Replit Secrets are properly configured and accessible

- [x] 5.0 Migrate Production System and Clean Up Legacy Code
  - [x] 5.1 Update `pyproject.toml` with minimal dependencies (remove unused packages)
  - [x] 5.2 Test new system alongside existing complex architecture
  - [x] 5.3 Switch Gunicorn workflow to use new simplified main.py
  - [x] 5.4 Verify production LINE webhook integration works with new system
  - [x] 5.5 Monitor system performance for 24 hours post-migration
  - [x] 5.6 Remove legacy files: `routes/`, `services/`, `utils/`, `prompts/` directories
  - [x] 5.7 Keep only 5 core files + configuration and documentation
  - [x] 5.8 Update `replit.md` with new simplified architecture documentation
  - [x] 5.9 Create deployment verification checklist for future reference