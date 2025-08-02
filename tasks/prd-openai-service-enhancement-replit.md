# Product Requirements Document: OpenAI Service Enhancement for Replit

## Introduction/Overview

This PRD outlines enhancements to the OpenAI service within the existing LINE chatbot serving Thai SMEs, deployed on Replit platform. The enhancements focus on three key areas: maintaining language consistency with user input, incorporating an Alex Hormozi-inspired persona for more impactful business advice, and implementing conversation memory to provide contextual responses throughout entire conversation sessions. This implementation leverages Replit's infrastructure while maintaining the current high-performance architecture.

## Goals

1. **Improve Language Consistency**: Ensure the chatbot responds in the same language as the user's latest input, creating a more natural conversation flow
2. **Enhance Advisory Impact**: Integrate Alex Hormozi's direct, value-focused communication style to deliver more actionable business advice
3. **Enable Contextual Conversations**: Implement conversation memory to maintain context throughout entire sessions, improving response relevance and user experience
4. **Maintain Performance**: Keep response times under 3 seconds while adding these enhancements
5. **Preserve Cultural Sensitivity**: Balance direct communication with Thai business etiquette
6. **Replit Optimization**: Implement within Replit's resource constraints and deployment capabilities

## User Stories

1. **As a Thai SME owner**, I want the chatbot to respond in Thai when I write in Thai, so that I can communicate naturally in my preferred language.

2. **As an English-speaking business owner in Thailand**, I want the chatbot to respond in English when I write in English, so that I don't need to translate responses.

3. **As a business owner seeking advice**, I want direct, actionable recommendations with specific metrics and frameworks, so that I can immediately implement improvements.

4. **As a user having a multi-turn conversation**, I want the chatbot to remember what we discussed earlier in the conversation, so that I don't need to repeat context and can have deeper discussions.

5. **As a Thai business owner**, I want advice that respects Thai business culture while still being direct and actionable, so that recommendations are both effective and culturally appropriate.

6. **As a developer on Replit**, I want the enhanced service to deploy seamlessly within the existing webhook architecture, so that deployment remains simple and reliable.

## Functional Requirements

### 1. Language Detection and Response System
1.1. The system must detect the language of each incoming user message using lightweight character-based detection (Unicode ranges for Thai, English, Japanese, Korean)
1.2. The system must support detection for: Thai, English, Japanese, and Korean
1.3. The system must respond in the same language as the user's latest message
1.4. The system must handle mixed-language inputs gracefully, defaulting to the dominant language
1.5. When language detection fails, the system must default to Thai (primary audience)
1.6. The detection logic must execute in <50ms to maintain performance targets

### 2. Alex Hormozi-Inspired Persona Integration
2.1. The system must incorporate the following communication characteristics:
   - Direct, no-nonsense communication style
   - Focus on value creation and specific ROI metrics
   - Challenge-based coaching that pushes users to take action
   - Use of proven business frameworks (e.g., value ladder, offer creation)
   - Emphasis on solving expensive problems for customers
2.2. The system must adapt Hormozi's style for Thai cultural context through dynamic prompt adjustment
2.3. The system must maintain a balance between directness and respect
2.4. The system must provide specific, measurable action items in responses
2.5. The persona implementation must be integrated into the system prompt without requiring separate API calls

### 3. Conversation Memory Management
3.1. The system must maintain conversation history for the entire session using in-memory storage
3.2. The system must include relevant conversation context in each OpenAI API call
3.3. The system must handle memory efficiently to avoid token limit issues through smart truncation
3.4. The system must clear memory after 1 hour of inactivity using session timeout management
3.5. The system must allow users to explicitly clear conversation history via special commands
3.6. The system must implement a sliding window approach if conversations exceed token limits
3.7. The memory storage must be optimized for Replit's memory constraints (<400MB target)

### 4. Performance and Optimization
4.1. The system must maintain response times under 3 seconds including all enhancements
4.2. The system must optimize token usage to control API costs through efficient context management
4.3. The system must implement efficient memory storage (in-memory for sessions)
4.4. The system must handle API failures gracefully with appropriate fallbacks
4.5. The system must maintain current health check performance (<100ms)

## Replit Deployment Specifications

- **Platform Type**: Webhook service (LINE Bot) - Always-on web application
- **Port Configuration**: 5000 (Flask with Gunicorn)
- **Workflow Command**: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`
- **Dependencies**: 
  - Existing: flask, gunicorn, openai, psutil, requests
  - New: langdetect (for language detection)
- **Environment Variables**: 
  - Existing: LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, SESSION_SECRET
  - No new environment variables required

## Database & Storage Requirements

- **Database Type**: No database required - In-memory session storage only
- **Storage Architecture**: Python dictionaries for conversation memory per LINE user ID
- **Session Management**: Automatic cleanup after 1-hour inactivity using background threading
- **Data Persistence**: Sessions are ephemeral (reset on application restart)
- **Memory Optimization**: Smart conversation truncation to stay within token limits

## Performance Requirements

- **Response Time Targets**: 
  - Health endpoint: <100ms (current: ~43ms)
  - Webhook processing: <3s total (including AI generation)
  - Language detection: <50ms
  - Memory operations: <10ms
- **Resource Constraints**: 
  - Memory usage: <400MB total
  - CPU: Optimized for single-core Replit environment
- **Scalability Needs**: Single-instance deployment supporting concurrent webhook requests
- **Monitoring**: Console logging with performance metrics and memory usage tracking

## External Integrations

- **APIs Required**: 
  - Azure OpenAI GPT-4.1-nano (existing)
  - LINE Messaging API (existing)
- **Authentication**: Existing Azure OpenAI API key and LINE webhook secrets
- **Rate Limits**: 
  - Azure OpenAI: Standard tier limits
  - LINE API: Webhook response within 30 seconds
- **Error Handling**: Graceful degradation to basic responses if enhanced features fail

## Security & Configuration

- **Secrets Management**: Use existing Replit secrets for API keys
- **Access Control**: LINE webhook signature verification (existing)
- **Data Privacy**: In-memory conversation data only, no persistent storage of user conversations
- **Memory Security**: Automatic session cleanup prevents data leakage between users

## Non-Goals (Out of Scope)

1. **Persistent conversation history across sessions** - Memory is session-based only
2. **Multiple persona options** - Only Alex Hormozi-inspired persona for this phase
3. **Voice message support** - Text-only conversations
4. **Multi-user conversation threads** - Each user has independent sessions
5. **Translation services** - The bot responds in detected language, not translating between languages
6. **Database storage for conversations** - Maintaining current database-free architecture
7. **External language detection APIs** - Using local detection only

## Replit Development Considerations

- **File Structure**: 
  - Enhanced `openai_service.py` for persona and memory management
  - New `language_detector.py` for language detection logic
  - Updated `app_simplified.py` for session management
- **Replit Features Used**: 
  - Secrets management for API keys
  - Always-on deployment for webhook availability
  - Console logging for debugging and monitoring
- **Testing Strategy**: 
  - Unit tests for language detection accuracy
  - Manual testing through LINE Bot interface
  - Performance monitoring through console logs
- **Debugging**: Enhanced console logging with conversation context and language detection results

## Success Metrics

1. **Language Consistency Rate**: >95% of responses match user's input language
2. **User Engagement**: 30% increase in average conversation length
3. **Action Implementation**: 40% of users report taking specific actions based on advice
4. **Response Time**: 95% of responses delivered in under 3 seconds
5. **User Satisfaction**: Positive feedback on directness and actionability of advice
6. **Context Relevance**: 90% reduction in users repeating information
7. **System Performance**: Maintain <400MB memory usage and <100ms health checks
8. **Language Detection Accuracy**: >90% correct language identification

## Deployment Checklist

- [ ] Install langdetect dependency via package manager
- [ ] Update OpenAI service with persona integration
- [ ] Implement language detection module
- [ ] Add conversation memory management
- [ ] Update webhook handler for session management
- [ ] Test language detection with Thai, English, Japanese, Korean inputs
- [ ] Verify conversation memory functionality
- [ ] Test Alex Hormozi persona responses
- [ ] Validate performance targets (<3s response time)
- [ ] Monitor memory usage during extended conversations
- [ ] Test session cleanup after inactivity
- [ ] Verify graceful error handling for all new features
- [ ] Ready for Replit deployment

## Open Questions

1. Should the system support voice message transcription in the future?
2. How should the system handle code-switching (users mixing languages in one message)?
3. Should there be different Hormozi intensity levels for different business stages?
4. What's the optimal conversation history length before pruning? (Recommend: 10-15 exchanges)
5. Should the system proactively suggest switching to user's preferred language?
6. How should the system handle Replit restarts that clear in-memory sessions?

## Implementation Notes

This enhancement maintains the current high-performance, database-free architecture while adding sophisticated conversation capabilities. The implementation prioritizes simplicity and leverages Replit's built-in features for a seamless deployment experience.