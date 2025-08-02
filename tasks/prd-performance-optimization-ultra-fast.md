# PRD: Ultra-Fast LINE Bot Performance Optimization

## Introduction/Overview

The current Replit-optimized LINE Bot, while simplified from 50+ files to 5 core files, still experiences response times of 0.7-1.5 seconds due to unnecessary language processing overhead and database connection pooling. This feature will eliminate language detection complexity and streamline the OpenAI integration to achieve sub-1-second response times while maintaining all business advisory capabilities.

**Goal**: Transform the LINE Bot to leverage LLM's natural language capabilities, removing artificial language constraints and processing overhead to deliver consistently fast responses under 1 second.

## Goals

1. **Reduce average response time** from 0.7-1.5s to 0.5-1.0s (primary goal)
2. **Eliminate language detection overhead** saving ~50ms per request
3. **Remove database connection pooling overhead** saving ~80ms per request  
4. **Simplify codebase** by removing language parameter complexity
5. **Maintain security and functionality** while optimizing performance
6. **Improve user experience** through natural language switching

## User Stories

### As a Thai SME Business Owner
- **I want** instant responses to my business questions in Thai
- **So that** I can get quick advice without waiting
- **Acceptance Criteria**: Response time consistently under 1 second, natural Thai responses

### As an English-speaking User  
- **I want** the bot to automatically respond in English when I write in English
- **So that** I don't need to configure language settings manually
- **Acceptance Criteria**: Seamless language switching without configuration

### As a Developer
- **I want** simplified code without language detection complexity
- **So that** I can easily maintain and debug the system
- **Acceptance Criteria**: Reduced lines of code (~520 to <450), lower cyclomatic complexity

### As a System Administrator
- **I want** optimal resource usage within Replit constraints
- **So that** the bot runs efficiently and cost-effectively
- **Acceptance Criteria**: Memory usage under 400MB, consistent sub-1s performance

## Functional Requirements

### FR1: Remove Language Parameter System
1. The system must eliminate the `language='th'` parameter from all OpenAI service methods
2. The system must remove language detection from webhook processing
3. The system must eliminate language-specific fallback messages
4. The system must remove language context passing between functions
5. The system must maintain error handling without language dependencies

### FR2: Implement Universal System Prompt
1. The system must create a single system prompt that works for all languages
2. The system must instruct the AI to respond in the user's input language
3. The system must maintain Thai SME business context without forcing Thai responses
4. The system must optimize prompt length for faster processing
5. The system must preserve business advisory capabilities

### FR3: Optimize Database Operations
1. The system must implement fire-and-forget logging using daemon threads
2. The system must remove connection pooling overhead for simple logging
3. The system must ensure database operations never block webhook responses
4. The system must maintain conversation history logging (optional)
5. The system must provide console-only logging as an alternative option

### FR4: Streamline Webhook Processing
1. The system must process webhooks with direct OpenAI calls
2. The system must maintain LINE signature verification for security
3. The system must eliminate unnecessary processing loops
4. The system must preserve async logging without blocking
5. The system must handle errors gracefully without exposing internals

### FR5: Performance Monitoring
1. The system must track response times before and after optimization
2. The system must monitor memory usage on Replit platform
3. The system must log performance metrics to console
4. The system must measure OpenAI API latency separately
5. The system must alert on performance degradation

## Non-Goals (Out of Scope)

1. **Advanced language features** - No Thai NLP, sentiment analysis, or complex language processing
2. **Multi-model AI integration** - No switching between different AI models or providers
3. **External caching systems** - No Redis or external cache implementations
4. **User authentication** - No login systems or session management
5. **Rich media optimization** - No complex file processing improvements
6. **Database schema changes** - No structural database modifications
7. **Third-party integrations** - No new external API connections

## Design Considerations

### System Architecture
The optimized architecture will follow this simplified flow:
```
LINE Webhook → Signature Verification → Direct OpenAI Call → Fire-and-forget Logging → Response
```

### OpenAI Integration
- Single universal system prompt replacing dual Thai/English prompts
- Remove timeout constraints to allow natural API completion
- Direct API calls without language parameter overhead
- Simplified error handling without language detection

### Database Strategy
- Option A: Minimal database with daemon thread logging (recommended)
- Option B: Console-only logging for maximum performance
- Remove connection pooling overhead
- Maintain security and data integrity

## Technical Considerations

### Replit Platform Constraints
- Must maintain memory usage under 512MB (currently ~300MB)
- Must keep file count under 10 core files
- Must respond to webhooks within 30 seconds
- Must use Replit console for logging visibility

### Security Requirements
- Must maintain LINE webhook signature verification
- Must secure API keys in Replit Secrets
- Must not expose internal error details
- Must implement basic input validation without overhead

### Compatibility Requirements
- Must maintain all existing OpenAI API integrations
- Must preserve current business advisory functionality
- Must work with existing Replit deployment process
- Must maintain backward compatibility with LINE API

## Success Metrics

### Primary Success Metrics
- **Average response time**: Reduce from 0.7-1.5s to 0.5-1.0s
- **Language detection overhead**: Eliminate ~50ms per request
- **Database connection overhead**: Reduce from ~100ms to <20ms
- **Memory usage**: Maintain under 400MB on Replit

### Secondary Success Metrics
- **Code complexity**: Reduce lines of code from ~520 to <450
- **Error rate**: Maintain under 0.5%
- **Language switching accuracy**: >95% natural language responses
- **Business advice relevance**: >90% contextually appropriate responses

### User Experience Metrics
- **Response accuracy**: >95% helpful responses
- **Natural language handling**: Seamless Thai/English switching
- **System uptime**: >99.9% availability
- **User satisfaction**: Faster, more natural conversations

## Open Questions

1. **Database logging trade-offs**: Should we implement console-only logging for maximum performance, or maintain database logging with daemon threads?

2. **OpenAI timeout handling**: Should we completely remove timeouts or set a higher limit (30 seconds) for complex queries?

3. **Performance monitoring depth**: Do we need real-time performance dashboards, or is console logging sufficient for monitoring?

4. **Rollback strategy**: Should we implement feature flags to quickly revert to the current system if issues arise?

5. **Testing approach**: What level of A/B testing is needed to validate language quality with the new universal prompt?

6. **Error handling granularity**: How detailed should error logging be without impacting performance?

7. **Memory optimization**: Are there additional memory optimizations we should consider beyond removing language detection?

8. **Deployment validation**: What specific performance benchmarks should we establish before considering the optimization complete?