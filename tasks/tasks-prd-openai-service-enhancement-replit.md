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

- [x] 1.0 Enhance OpenAI Service with Language Detection and Alex Hormozi Persona
  - [x] 1.1 Update system prompt with explicit language detection rules (Thai, English, Japanese, Korean)
  - [x] 1.2 Integrate Alex Hormozi communication characteristics (direct, value-focused, action-oriented)
  - [x] 1.3 Add Thai cultural adaptation layer to balance directness with respect
  - [x] 1.4 Add conversation context injection capability to system prompt
  - [x] 1.5 Update generate_response method to accept conversation history parameter
  - [x] 1.6 Test system prompt effectiveness with sample multilingual inputs

- [x] 2.0 Implement Conversation Memory Management System
  - [x] 2.1 Create global session storage dictionary with user_id as key
  - [x] 2.2 Add conversation history tracking with message timestamps
  - [x] 2.3 Implement sliding window approach for token limit management
  - [x] 2.4 Add session timeout logic (1-hour inactivity cleanup)
  - [x] 2.5 Create utility functions for session CRUD operations
  - [x] 2.6 Add memory optimization to stay within 400MB Replit constraint
  - [x] 2.7 Implement conversation history formatting for OpenAI context injection

- [x] 3.0 Update Webhook Handler for Session Management
  - [x] 3.1 Extract and store user_id for session tracking in webhook handler
  - [x] 3.2 Retrieve conversation history before OpenAI API call
  - [x] 3.3 Update conversation history after receiving OpenAI response
  - [x] 3.4 Integrate session cleanup into webhook processing
  - [x] 3.5 Add error handling for session storage failures
  - [x] 3.6 Update logging to include conversation context indicators

- [x] 4.0 Add Enhanced Performance Monitoring and Logging
  - [x] 4.1 Add conversation memory usage tracking to performance logs
  - [x] 4.2 Monitor token usage and conversation length metrics
  - [x] 4.3 Track language consistency (response matches input language)
  - [x] 4.4 Add session management performance metrics
  - [x] 4.5 Enhanced debug logging for conversation context and persona responses
  - [x] 4.6 Add memory cleanup statistics to health endpoint

- [x] 5.0 Test and Validate All Enhancements
  - [x] 5.1 Test language detection and response consistency (Thai, English, Japanese, Korean)
  - [x] 5.2 Test conversation memory across multi-turn conversations
  - [x] 5.3 Test Alex Hormozi persona effectiveness and Thai cultural adaptation
  - [x] 5.4 Validate session timeout and cleanup functionality
  - [x] 5.5 Performance testing to ensure <3s response time maintained
  - [x] 5.6 Memory usage validation during extended conversations
  - [x] 5.7 Test graceful error handling for all new features