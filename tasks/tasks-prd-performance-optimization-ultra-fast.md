# Task List: Ultra-Fast LINE Bot Performance Optimization

## Relevant Files

- `openai_service.py` - Contains language parameter logic and separate Thai/English prompts that need to be unified
- `app_simplified.py` - Main webhook handler that currently passes language parameters and needs streamlining
- `database.py` - Database service with connection pooling overhead that needs fire-and-forget optimization
- `line_service.py` - LINE API integration that may need timeout adjustments for optimization
- `main.py` - Entry point that may need minimal updates for performance monitoring

### Notes

- Focus on eliminating language detection overhead (~50ms savings per request)
- Remove database connection pooling overhead (~80ms savings per request)
- Target overall response time reduction from 0.7-1.5s to 0.5-1.0s
- Maintain all existing security (signature verification) and functionality
- Keep codebase under 10 files and memory usage under 400MB per Replit constraints

## Tasks

- [ ] 1.0 Remove Language Parameter System
  - [ ] 1.1 Remove `language` parameter from `generate_response()` method in `openai_service.py`
  - [ ] 1.2 Update `app_simplified.py` webhook handler to stop passing `'th'` language parameter
  - [ ] 1.3 Remove language-specific fallback messages from `openai_service.py`
  - [ ] 1.4 Remove any language detection logic from webhook processing flow
  - [ ] 1.5 Update function signatures and method calls to eliminate language context passing

- [ ] 2.0 Implement Universal System Prompt
  - [ ] 2.1 Replace separate Thai/English system prompts with single universal prompt in `openai_service.py`
  - [ ] 2.2 Design universal prompt that instructs AI to respond in user's input language
  - [ ] 2.3 Preserve Thai SME business context without forcing Thai responses
  - [ ] 2.4 Optimize prompt length for faster OpenAI processing (~50ms target savings)
  - [ ] 2.5 Test universal prompt with both Thai and English inputs to ensure quality

- [ ] 3.0 Optimize Database Operations with Fire-and-Forget Logging
  - [ ] 3.1 Remove `ThreadedConnectionPool` from `database.py` to eliminate connection overhead
  - [ ] 3.2 Implement direct database connection with daemon thread for fire-and-forget logging
  - [ ] 3.3 Ensure database operations never block webhook response (~80ms target savings)
  - [ ] 3.4 Add console-only logging option as alternative to database logging
  - [ ] 3.5 Verify async logging maintains conversation history without performance impact

- [ ] 4.0 Streamline Webhook Processing Flow
  - [ ] 4.1 Remove OpenAI timeout constraints or increase to 30 seconds in `openai_service.py`
  - [ ] 4.2 Eliminate unnecessary processing loops in `app_simplified.py` webhook handler
  - [ ] 4.3 Maintain LINE signature verification for security without performance impact
  - [ ] 4.4 Optimize error handling to avoid language-dependent fallback logic
  - [ ] 4.5 Implement direct OpenAI call flow: Webhook → Verification → OpenAI → Response

- [ ] 5.0 Performance Monitoring and Validation
  - [ ] 5.1 Add response time tracking with start/end timestamps in webhook handler
  - [ ] 5.2 Add memory usage monitoring for Replit constraints (target <400MB)
  - [ ] 5.3 Log performance metrics to console for Replit visibility
  - [ ] 5.4 Measure and log OpenAI API latency separately from total response time
  - [ ] 5.5 Validate performance improvements meet target: 0.7-1.5s → 0.5-1.0s response time