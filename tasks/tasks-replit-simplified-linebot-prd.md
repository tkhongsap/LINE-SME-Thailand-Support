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
- [ ] 2.0 Implement Direct API Integrations  
- [ ] 3.0 Set Up Replit-Optimized Database Layer
- [ ] 4.0 Test and Validate Performance in Replit Environment
- [ ] 5.0 Migrate Production System and Clean Up Legacy Code