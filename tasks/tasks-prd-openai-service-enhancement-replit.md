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
  - [ ] 1.1 Update system prompt with explicit language detection rules (Thai, English, Japanese, Korean)
  - [ ] 1.2 Integrate Alex Hormozi communication characteristics (direct, value-focused, action-oriented)
  - [ ] 1.3 Add Thai cultural adaptation layer to balance directness with respect
  - [ ] 1.4 Add conversation context injection capability to system prompt
  - [ ] 1.5 Update generate_response method to accept conversation history parameter
  - [ ] 1.6 Test system prompt effectiveness with sample multilingual inputs

- [ ] 2.0 Implement Conversation Memory Management System
  - [ ] 2.1 Create global session storage dictionary with user_id as key
  - [ ] 2.2 Add conversation history tracking with message timestamps
  - [ ] 2.3 Implement sliding window approach for token limit management
  - [ ] 2.4 Add session timeout logic (1-hour inactivity cleanup)
  - [ ] 2.5 Create utility functions for session CRUD operations
  - [ ] 2.6 Add memory optimization to stay within 400MB Replit constraint
  - [ ] 2.7 Implement conversation history formatting for OpenAI context injection

- [ ] 3.0 Update Webhook Handler for Session Management
  - [ ] 3.1 Extract and store user_id for session tracking in webhook handler
  - [ ] 3.2 Retrieve conversation history before OpenAI API call
  - [ ] 3.3 Update conversation history after receiving OpenAI response
  - [ ] 3.4 Integrate session cleanup into webhook processing
  - [ ] 3.5 Add error handling for session storage failures
  - [ ] 3.6 Update logging to include conversation context indicators

- [ ] 4.0 Add Enhanced Performance Monitoring and Logging
  - [ ] 4.1 Add conversation memory usage tracking to performance logs
  - [ ] 4.2 Monitor token usage and conversation length metrics
  - [ ] 4.3 Track language consistency (response matches input language)
  - [ ] 4.4 Add session management performance metrics
  - [ ] 4.5 Enhanced debug logging for conversation context and persona responses
  - [ ] 4.6 Add memory cleanup statistics to health endpoint

- [ ] 5.0 Test and Validate All Enhancements
  - [ ] 5.1 Test language detection and response consistency (Thai, English, Japanese, Korean)
  - [ ] 5.2 Test conversation memory across multi-turn conversations
  - [ ] 5.3 Test Alex Hormozi persona effectiveness and Thai cultural adaptation
  - [ ] 5.4 Validate session timeout and cleanup functionality
  - [ ] 5.5 Performance testing to ensure <3s response time maintained
  - [ ] 5.6 Memory usage validation during extended conversations
  - [ ] 5.7 Test graceful error handling for all new features