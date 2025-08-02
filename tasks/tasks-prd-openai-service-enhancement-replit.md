# Tasks: OpenAI Service Enhancement for Replit

Based on PRD: `tasks/prd-openai-service-enhancement-replit.md`

## Current State Assessment

**Existing Infrastructure:**
- `openai_service.py`: Basic Azure OpenAI integration with simple system prompt
- `app_simplified.py`: Webhook handler with performance monitoring
- `line_service.py`: LINE API wrapper for message sending
- Database-free architecture with console logging
- Ultra-fast response times (43ms health, ~3s webhook)

**Enhancement Requirements:**
- Language-aware system prompt with Alex Hormozi persona
- In-memory conversation history management
- Session-based user context tracking
- Performance monitoring for enhanced features
- Cultural adaptation for Thai SME market

## Relevant Files

- `openai_service.py` - Core service requiring system prompt enhancement and conversation memory integration
- `app_simplified.py` - Webhook handler needing session management and enhanced logging
- `line_service.py` - Existing LINE API service (minimal changes expected)
- `main.py` - Gunicorn entry point (no changes required)

### Notes

- No new dependencies required - leveraging existing Flask, OpenAI, and psutil packages
- In-memory storage approach maintains database-free architecture
- All enhancements must preserve <3s response time target
- Testing will be manual through LINE Bot interface

## Tasks

- [ ] 1.0 Enhance OpenAI Service with Language Detection and Alex Hormozi Persona
- [ ] 2.0 Implement Conversation Memory Management System  
- [ ] 3.0 Update Webhook Handler for Session Management
- [ ] 4.0 Add Enhanced Performance Monitoring and Logging
- [ ] 5.0 Test and Validate All Enhancements