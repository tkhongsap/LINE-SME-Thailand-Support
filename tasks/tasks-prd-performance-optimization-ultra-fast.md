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
- [ ] 2.0 Implement Universal System Prompt
- [ ] 3.0 Optimize Database Operations with Fire-and-Forget Logging
- [ ] 4.0 Streamline Webhook Processing Flow
- [ ] 5.0 Performance Monitoring and Validation