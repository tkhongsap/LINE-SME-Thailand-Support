# Product Requirements Document: OpenAI Service Enhancement

## Introduction/Overview

This PRD outlines enhancements to the OpenAI service for a LINE chatbot serving Thai SMEs. The enhancements focus on three key areas: maintaining language consistency with user input, incorporating an Alex Hormozi-inspired persona for more impactful business advice, and implementing conversation memory to provide contextual responses throughout entire conversation sessions.

## Goals

1. **Improve Language Consistency**: Ensure the chatbot responds in the same language as the user's latest input, creating a more natural conversation flow
2. **Enhance Advisory Impact**: Integrate Alex Hormozi's direct, value-focused communication style to deliver more actionable business advice
3. **Enable Contextual Conversations**: Implement conversation memory to maintain context throughout entire sessions, improving response relevance and user experience
4. **Maintain Performance**: Keep response times under 3 seconds while adding these enhancements
5. **Preserve Cultural Sensitivity**: Balance direct communication with Thai business etiquette

## User Stories

1. **As a Thai SME owner**, I want the chatbot to respond in Thai when I write in Thai, so that I can communicate naturally in my preferred language.

2. **As an English-speaking business owner in Thailand**, I want the chatbot to respond in English when I write in English, so that I don't need to translate responses.

3. **As a business owner seeking advice**, I want direct, actionable recommendations with specific metrics and frameworks, so that I can immediately implement improvements.

4. **As a user having a multi-turn conversation**, I want the chatbot to remember what we discussed earlier in the conversation, so that I don't need to repeat context and can have deeper discussions.

5. **As a Thai business owner**, I want advice that respects Thai business culture while still being direct and actionable, so that recommendations are both effective and culturally appropriate.

## Functional Requirements

### 1. Language Detection and Response System
1.1. The system must detect the language of each incoming user message
1.2. The system must support detection for: Thai, English, Japanese, and Korean
1.3. The system must respond in the same language as the user's latest message
1.4. The system must handle mixed-language inputs gracefully
1.5. When language detection fails, the system must default to Thai (primary audience)

### 2. Alex Hormozi-Inspired Persona Integration
2.1. The system must incorporate the following communication characteristics:
   - Direct, no-nonsense communication style
   - Focus on value creation and specific ROI metrics
   - Challenge-based coaching that pushes users to take action
   - Use of proven business frameworks (e.g., value ladder, offer creation)
   - Emphasis on solving expensive problems for customers
2.2. The system must adapt Hormozi's style for Thai cultural context
2.3. The system must maintain a balance between directness and respect
2.4. The system must provide specific, measurable action items in responses

### 3. Conversation Memory Management
3.1. The system must maintain conversation history for the entire session
3.2. The system must include relevant conversation context in each API call
3.3. The system must handle memory efficiently to avoid token limit issues
3.4. The system must clear memory after 1 hour of inactivity
3.5. The system must allow users to explicitly clear conversation history
3.6. The system must implement a sliding window approach if conversations exceed token limits

### 4. Performance and Optimization
4.1. The system must maintain response times under 3 seconds
4.2. The system must optimize token usage to control API costs
4.3. The system must implement efficient memory storage (in-memory for sessions)
4.4. The system must handle API failures gracefully with appropriate fallbacks

## Non-Goals (Out of Scope)

1. **Persistent conversation history across sessions** - Memory is session-based only
2. **Multiple persona options** - Only Alex Hormozi-inspired persona for this phase
3. **Voice message support** - Text-only conversations
4. **Multi-user conversation threads** - Each user has independent sessions
5. **Translation services** - The bot responds in detected language, not translating between languages

## Design Considerations

### System Prompt Structure
- Dynamic language instruction based on detected input language
- Hormozi-inspired characteristics embedded in base prompt
- Context injection for conversation history
- Cultural adaptation layer for Thai market

### Memory Architecture
- In-memory conversation buffer per user session
- Efficient storage format to minimize token usage
- Automatic pruning of older messages if approaching limits
- Session timeout handling with graceful cleanup

### Language Detection Algorithm
- Character-based detection for Asian languages (Unicode ranges)
- Fallback to simple heuristics for edge cases
- Confidence scoring to handle mixed-language inputs

## Technical Considerations

1. **Token Optimization**: Implement smart truncation for long conversations
2. **Caching Strategy**: Consider caching common responses for efficiency
3. **Error Handling**: Graceful degradation if memory or language detection fails
4. **Monitoring**: Track language detection accuracy and memory usage
5. **Testing**: Comprehensive tests for multi-language scenarios and edge cases

## Success Metrics

1. **Language Consistency Rate**: >95% of responses match user's input language
2. **User Engagement**: 30% increase in average conversation length
3. **Action Implementation**: 40% of users report taking specific actions based on advice
4. **Response Time**: 95% of responses delivered in under 3 seconds
5. **User Satisfaction**: Positive feedback on directness and actionability of advice
6. **Context Relevance**: 90% reduction in users repeating information

## Open Questions

1. Should the system support voice message transcription in the future?
2. How should the system handle code-switching (users mixing languages in one message)?
3. Should there be different Hormozi intensity levels for different business stages?
4. What's the optimal conversation history length before pruning?
5. Should the system proactively suggest switching to user's preferred language?