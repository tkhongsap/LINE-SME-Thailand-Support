"""
AI Optimization utilities for Azure OpenAI integration
Implements advanced optimization strategies for the Thai SME Support chatbot
"""

import logging
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict
import numpy as np
from functools import lru_cache
import asyncio
from dataclasses import dataclass
from enum import Enum
import threading
import redis
import pickle
from config import Config

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelType(Enum):
    """Model types with associated costs and capabilities"""
    GPT4_TURBO = "gpt-4-turbo"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-35-turbo"
    
    @property
    def cost_per_1k_tokens(self) -> Dict[str, float]:
        """Cost per 1K tokens for input/output"""
        costs = {
            ModelType.GPT4_TURBO: {"input": 0.01, "output": 0.03},
            ModelType.GPT4: {"input": 0.03, "output": 0.06},
            ModelType.GPT35_TURBO: {"input": 0.0015, "output": 0.002}
        }
        return costs[self]
    
    @property
    def max_tokens(self) -> int:
        """Maximum token limit for each model"""
        limits = {
            ModelType.GPT4_TURBO: 128000,
            ModelType.GPT4: 8192,
            ModelType.GPT35_TURBO: 16384
        }
        return limits[self]


@dataclass
class TokenUsage:
    """Track token usage for cost optimization"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    model: str
    timestamp: datetime


class ContextOptimizer:
    """Optimize conversation context for token efficiency"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.importance_weights = {
            'user': 1.0,
            'assistant': 0.8,
            'system': 1.2
        }
    
    def compress_context(self, messages: List[Dict], target_tokens: int) -> List[Dict]:
        """Compress conversation context to fit within token limit"""
        if not messages:
            return []
        
        # Calculate importance scores
        scored_messages = []
        for i, msg in enumerate(messages):
            # Recent messages are more important
            recency_score = 1.0 - (i / len(messages)) * 0.5
            
            # Role-based importance
            role_score = self.importance_weights.get(msg['role'], 0.5)
            
            # Content length penalty (prefer shorter messages)
            length_penalty = 1.0 / (1.0 + len(msg['content']) / 1000)
            
            # Combined score
            score = recency_score * role_score * length_penalty
            
            scored_messages.append({
                'message': msg,
                'score': score,
                'tokens': self._estimate_tokens(msg['content'])
            })
        
        # Sort by score and select messages within token limit
        scored_messages.sort(key=lambda x: x['score'], reverse=True)
        
        selected_messages = []
        total_tokens = 0
        
        for item in scored_messages:
            if total_tokens + item['tokens'] <= target_tokens:
                selected_messages.append(item['message'])
                total_tokens += item['tokens']
        
        # Maintain chronological order
        selected_messages.sort(key=lambda x: messages.index(x))
        
        return selected_messages
    
    def summarize_old_context(self, messages: List[Dict], keep_recent: int = 5) -> Optional[str]:
        """Summarize older messages to preserve context"""
        if len(messages) <= keep_recent:
            return None
        
        old_messages = messages[:-keep_recent]
        
        # Extract key information
        topics = set()
        questions = []
        decisions = []
        
        for msg in old_messages:
            content = msg['content'].lower()
            
            # Extract topics (simple keyword extraction)
            if any(keyword in content for keyword in ['ธุรกิจ', 'business', 'sme', 'การตลาด', 'marketing']):
                topics.add('business')
            if any(keyword in content for keyword in ['การเงิน', 'finance', 'loan', 'เงินกู้']):
                topics.add('finance')
            if any(keyword in content for keyword in ['ภาษี', 'tax', 'บัญชี', 'accounting']):
                topics.add('tax/accounting')
            
            # Extract questions
            if '?' in content or any(q in content for q in ['อย่างไร', 'how', 'what', 'ทำไม']):
                questions.append(content[:100])
        
        # Build summary
        summary_parts = []
        if topics:
            summary_parts.append(f"Previous topics discussed: {', '.join(topics)}")
        if questions:
            summary_parts.append(f"Key questions asked: {len(questions)} questions about business operations")
        
        return ' '.join(summary_parts) if summary_parts else None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Thai text typically uses more tokens
        if any('\u0E00' <= char <= '\u0E7F' for char in text):
            return int(len(text) * 0.7)  # Thai characters
        return int(len(text) * 0.25)  # English approximation


class ResponseCache:
    """Intelligent response caching with semantic similarity"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.memory_cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.hit_count = 0
        self.miss_count = 0
        
        # Initialize Redis for distributed caching
        self.redis_client = None
        try:
            self.redis_client = redis.Redis.from_url(
                Config.REDIS_URL,
                decode_responses=False,  # We'll handle binary data
                socket_timeout=2,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            self.redis_client = None
    
    def get_cache_key(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from prompt and context"""
        cache_data = {
            'prompt': prompt.lower().strip(),
            'context': context or {}
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, prompt: str, context: Optional[Dict] = None) -> Optional[str]:
        """Get cached response if available and valid"""
        key = self.get_cache_key(prompt, context)
        
        # Check memory cache first (fastest)
        if key in self.memory_cache:
            entry_time = self.access_times[key]
            if datetime.utcnow() - entry_time < self.ttl:
                self.hit_count += 1
                logger.debug(f"Memory cache hit for prompt: {prompt[:50]}...")
                return self.memory_cache[key]
            else:
                # Remove expired entry
                del self.memory_cache[key]
                del self.access_times[key]
        
        # Check Redis cache (distributed)
        if self.redis_client:
            try:
                redis_key = f"ai_response:{key}"
                cached_data = self.redis_client.get(redis_key)
                if cached_data:
                    response_data = pickle.loads(cached_data)
                    response = response_data['response']
                    
                    # Promote to memory cache for faster subsequent access
                    self.memory_cache[key] = response
                    self.access_times[key] = datetime.utcnow()
                    
                    self.hit_count += 1
                    logger.info(f"Redis cache hit for prompt: {prompt[:50]}...")
                    return response
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Check for similar responses (semantic caching)
        similar_response = self.find_similar(prompt, threshold=0.85)
        if similar_response:
            self.hit_count += 1
            logger.info(f"Semantic cache hit for prompt: {prompt[:50]}...")
            return similar_response
        
        self.miss_count += 1
        
        return None
    
    def set(self, prompt: str, response: str, context: Optional[Dict] = None):
        """Cache a response"""
        key = self.get_cache_key(prompt, context)
        
        current_time = datetime.utcnow()
        
        # Implement LRU if memory cache is full
        if len(self.memory_cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.memory_cache[oldest_key]
            del self.access_times[oldest_key]
        
        # Store in memory cache
        self.memory_cache[key] = response
        self.access_times[key] = current_time
        
        # Store in Redis with TTL
        if self.redis_client:
            try:
                redis_key = f"ai_response:{key}"
                cache_data = {
                    'response': response,
                    'timestamp': current_time.isoformat(),
                    'prompt_hash': key,
                    'context': context or {}
                }
                
                # Set with TTL in seconds
                ttl_seconds = int(self.ttl.total_seconds())
                self.redis_client.setex(
                    redis_key,
                    ttl_seconds,
                    pickle.dumps(cache_data)
                )
                logger.debug(f"Cached to Redis with TTL {ttl_seconds}s: {prompt[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to cache to Redis: {e}")
        
        logger.info(f"Cached response for prompt: {prompt[:50]}...")
    
    def find_similar(self, prompt: str, threshold: float = 0.8) -> Optional[str]:
        """Find similar cached prompts (simple similarity for now)"""
        prompt_lower = prompt.lower().strip()
        
        for cached_key, response in self.memory_cache.items():
            # For semantic similarity, we'd need the original prompt
            # For now, skip similarity matching and focus on exact matches
            # TODO: Store original prompts for better semantic matching
            pass
        
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / max(1, total_requests)) * 100
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': round(hit_rate, 2),
            'memory_cache_size': len(self.memory_cache),
            'max_cache_size': self.max_size,
            'cache_utilization_percent': round((len(self.memory_cache) / self.max_size) * 100, 2),
            'redis_available': self.redis_client is not None,
            'ttl_hours': self.ttl.total_seconds() / 3600
        }
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if pattern:
            # Clear specific pattern from memory cache
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                del self.access_times[key]
            
            # Clear from Redis
            if self.redis_client:
                try:
                    redis_pattern = f"ai_response:*{pattern}*"
                    keys = self.redis_client.keys(redis_pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        logger.info(f"Cleared {len(keys)} Redis cache entries matching '{pattern}'")
                except Exception as e:
                    logger.warning(f"Failed to clear Redis cache: {e}")
        else:
            # Clear all caches
            self.memory_cache.clear()
            self.access_times.clear()
            self.hit_count = 0
            self.miss_count = 0
            
            if self.redis_client:
                try:
                    keys = self.redis_client.keys("ai_response:*")
                    if keys:
                        self.redis_client.delete(*keys)
                        logger.info(f"Cleared {len(keys)} Redis cache entries")
                except Exception as e:
                    logger.warning(f"Failed to clear Redis cache: {e}")
        
        logger.info("Cache cleared successfully")


class AdvancedRateLimiter:
    """Advanced rate limiter with adaptive throttling and circuit breaker"""
    
    def __init__(self, 
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 tokens_per_minute: int = 50000,
                 circuit_breaker_threshold: int = 10,
                 circuit_breaker_timeout: int = 300):
        
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.tokens_per_minute = tokens_per_minute
        
        # Sliding window counters
        self.request_timestamps = deque()
        self.token_usage_window = deque()
        self.hourly_requests = deque()
        
        # Circuit breaker
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.consecutive_failures = 0
        self.circuit_open_time = None
        self.circuit_state = 'closed'  # closed, open, half-open
        
        # Adaptive throttling
        self.current_load = 0.0  # 0.0 to 1.0
        self.response_times = deque(maxlen=100)
        self.error_count = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Advanced rate limiter initialized: {requests_per_minute} req/min, {tokens_per_minute} tokens/min")
    
    def check_rate_limit(self, estimated_tokens: int = 1000) -> Tuple[bool, float]:
        """
        Check if request can proceed based on rate limits
        
        Returns:
            Tuple[bool, float]: (can_proceed, wait_time_seconds)
        """
        with self.lock:
            current_time = time.time()
            
            # Check circuit breaker
            if not self._check_circuit_breaker():
                return False, self.circuit_breaker_timeout
            
            # Clean old entries
            self._cleanup_old_entries(current_time)
            
            # Check minute-based request limit
            recent_requests = len(self.request_timestamps)
            if recent_requests >= self.requests_per_minute:
                wait_time = 60 - (current_time - self.request_timestamps[0])
                return False, max(0, wait_time)
            
            # Check hourly request limit
            if len(self.hourly_requests) >= self.requests_per_hour:
                oldest_hour_request = self.hourly_requests[0]
                wait_time = 3600 - (current_time - oldest_hour_request)
                return False, max(0, wait_time)
            
            # Check token limit
            current_token_usage = sum(usage[1] for usage in self.token_usage_window)
            if current_token_usage + estimated_tokens > self.tokens_per_minute:
                # Find when we can proceed
                tokens_needed = estimated_tokens
                for i, (timestamp, tokens) in enumerate(self.token_usage_window):
                    if current_time - timestamp >= 60:
                        continue
                    if current_token_usage - tokens + estimated_tokens <= self.tokens_per_minute:
                        wait_time = 60 - (current_time - timestamp)
                        return False, max(0, wait_time)
                
                # If we can't find a suitable slot, wait for the oldest entry to expire
                if self.token_usage_window:
                    wait_time = 60 - (current_time - self.token_usage_window[0][0])
                    return False, max(0, wait_time)
            
            # Apply adaptive throttling based on current load
            if self.current_load > 0.8:  # High load
                adaptive_delay = min(5.0, (self.current_load - 0.8) * 10)
                return False, adaptive_delay
            
            return True, 0.0
    
    def record_request(self, tokens_used: int, response_time: float, success: bool):
        """Record a completed request for rate limiting and adaptive throttling"""
        with self.lock:
            current_time = time.time()
            
            # Record request
            self.request_timestamps.append(current_time)
            self.hourly_requests.append(current_time)
            self.token_usage_window.append((current_time, tokens_used))
            
            # Record response time
            self.response_times.append(response_time)
            
            # Update circuit breaker state
            if success:
                self.consecutive_failures = 0
                if self.circuit_state == 'half-open':
                    self.circuit_state = 'closed'
                    logger.info("Circuit breaker closed - service recovered")
            else:
                self.consecutive_failures += 1
                self.error_count += 1
                
                if (self.consecutive_failures >= self.circuit_breaker_threshold and 
                    self.circuit_state == 'closed'):
                    self._open_circuit_breaker()
            
            # Update current load based on response times and error rate
            self._update_load_metrics()
            
            # Cleanup old entries
            self._cleanup_old_entries(current_time)
    
    def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker state"""
        current_time = time.time()
        
        if self.circuit_state == 'open':
            if (self.circuit_open_time and 
                current_time - self.circuit_open_time > self.circuit_breaker_timeout):
                self.circuit_state = 'half-open'
                logger.info("Circuit breaker half-open - testing service")
                return True
            return False
        
        return True
    
    def _open_circuit_breaker(self):
        """Open circuit breaker due to too many failures"""
        self.circuit_state = 'open'
        self.circuit_open_time = time.time()
        logger.warning(f"Circuit breaker opened after {self.consecutive_failures} consecutive failures")
    
    def _update_load_metrics(self):
        """Update current load based on response times and error rates"""
        if not self.response_times:
            self.current_load = 0.0
            return
        
        # Calculate load based on response time
        avg_response_time = sum(self.response_times) / len(self.response_times)
        response_load = min(1.0, avg_response_time / 10.0)  # Normalize to 10s max
        
        # Calculate load based on error rate
        total_requests = len(self.request_timestamps)
        error_rate = self.error_count / max(1, total_requests)
        error_load = min(1.0, error_rate * 2)  # 50% error rate = full load
        
        # Calculate load based on request rate
        recent_requests = len([t for t in self.request_timestamps if time.time() - t < 60])
        rate_load = recent_requests / self.requests_per_minute
        
        # Combined load (weighted average)
        self.current_load = (response_load * 0.4 + error_load * 0.3 + rate_load * 0.3)
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than their respective windows"""
        # Clean minute-based entries
        while (self.request_timestamps and 
               current_time - self.request_timestamps[0] > 60):
            self.request_timestamps.popleft()
        
        # Clean hourly entries
        while (self.hourly_requests and 
               current_time - self.hourly_requests[0] > 3600):
            self.hourly_requests.popleft()
        
        # Clean token usage entries
        while (self.token_usage_window and 
               current_time - self.token_usage_window[0][0] > 60):
            self.token_usage_window.popleft()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics"""
        with self.lock:
            current_time = time.time()
            self._cleanup_old_entries(current_time)
            
            recent_requests = len(self.request_timestamps)
            hourly_requests = len(self.hourly_requests)
            current_tokens = sum(usage[1] for usage in self.token_usage_window)
            
            avg_response_time = (sum(self.response_times) / len(self.response_times) 
                               if self.response_times else 0)
            
            return {
                'current_load': round(self.current_load, 3),
                'circuit_state': self.circuit_state,
                'consecutive_failures': self.consecutive_failures,
                'requests_last_minute': recent_requests,
                'requests_last_hour': hourly_requests,
                'tokens_last_minute': current_tokens,
                'limits': {
                    'requests_per_minute': self.requests_per_minute,
                    'requests_per_hour': self.requests_per_hour,
                    'tokens_per_minute': self.tokens_per_minute
                },
                'utilization': {
                    'minute_requests_percent': round((recent_requests / self.requests_per_minute) * 100, 1),
                    'hourly_requests_percent': round((hourly_requests / self.requests_per_hour) * 100, 1),
                    'tokens_percent': round((current_tokens / self.tokens_per_minute) * 100, 1)
                },
                'performance': {
                    'avg_response_time_ms': round(avg_response_time * 1000, 1),
                    'error_count': self.error_count
                }
            }


class RequestOptimizer:
    """Optimize API requests with batching and deduplication"""
    
    def __init__(self, batch_window_ms: int = 100, max_batch_size: int = 5):
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        self.pending_requests = deque()
        self.request_hashes = set()
        self._batch_task = None
    
    def deduplicate_request(self, request_data: Dict) -> bool:
        """Check if request is duplicate"""
        request_hash = hashlib.md5(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()
        
        if request_hash in self.request_hashes:
            logger.info("Duplicate request detected, skipping")
            return True
        
        self.request_hashes.add(request_hash)
        # Clean old hashes periodically (simple approach)
        if len(self.request_hashes) > 1000:
            self.request_hashes.clear()
        
        return False
    
    async def batch_requests(self, requests: List[Dict]) -> List[Dict]:
        """Batch multiple requests for efficiency"""
        if len(requests) == 1:
            return requests
        
        # Group similar requests
        grouped = defaultdict(list)
        for req in requests:
            # Group by model and temperature
            key = (req.get('model', ''), req.get('temperature', 0.7))
            grouped[key].append(req)
        
        batched_requests = []
        for group_key, group_requests in grouped.items():
            if len(group_requests) > 1:
                # Combine prompts for batch processing
                combined_prompt = "\n---\n".join([
                    f"Query {i+1}: {req['messages'][-1]['content']}"
                    for i, req in enumerate(group_requests)
                ])
                
                batched_request = group_requests[0].copy()
                batched_request['messages'][-1]['content'] = combined_prompt
                batched_request['_batch_size'] = len(group_requests)
                batched_requests.append(batched_request)
                
                logger.info(f"Batched {len(group_requests)} requests")
            else:
                batched_requests.extend(group_requests)
        
        return batched_requests


class ModelSelector:
    """Dynamic model selection based on task complexity and cost"""
    
    def __init__(self, cost_threshold_daily: float = 10.0):
        self.cost_threshold_daily = cost_threshold_daily
        self.daily_costs = defaultdict(float)
        self.task_patterns = {
            'simple_greeting': ModelType.GPT35_TURBO,
            'business_advice': ModelType.GPT4,
            'document_analysis': ModelType.GPT4_TURBO,
            'image_analysis': ModelType.GPT4
        }
    
    def select_model(self, task_type: str, prompt_complexity: float, 
                    user_tier: str = 'free') -> ModelType:
        """Select optimal model based on task and constraints"""
        # Check daily cost limit
        today = datetime.utcnow().date()
        if self.daily_costs[today] >= self.cost_threshold_daily:
            logger.warning("Daily cost threshold reached, using cheaper model")
            return ModelType.GPT35_TURBO
        
        # Task-based selection
        if task_type in self.task_patterns:
            return self.task_patterns[task_type]
        
        # Complexity-based selection
        if prompt_complexity < 0.3:
            return ModelType.GPT35_TURBO
        elif prompt_complexity < 0.7:
            return ModelType.GPT4
        else:
            return ModelType.GPT4_TURBO
    
    def estimate_task_complexity(self, prompt: str, has_context: bool = False) -> float:
        """Estimate task complexity from prompt"""
        complexity_score = 0.0
        
        # Length factor
        if len(prompt) > 500:
            complexity_score += 0.3
        elif len(prompt) > 200:
            complexity_score += 0.2
        
        # Keyword analysis
        complex_keywords = ['analyze', 'วิเคราะห์', 'evaluate', 'ประเมิน', 
                          'strategy', 'กลยุทธ์', 'financial', 'การเงิน']
        simple_keywords = ['hello', 'สวัสดี', 'thank', 'ขอบคุณ', 'yes', 'ใช่']
        
        prompt_lower = prompt.lower()
        for keyword in complex_keywords:
            if keyword in prompt_lower:
                complexity_score += 0.15
        
        for keyword in simple_keywords:
            if keyword in prompt_lower:
                complexity_score -= 0.1
        
        # Context factor
        if has_context:
            complexity_score += 0.2
        
        # Normalize score
        return max(0.0, min(1.0, complexity_score))
    
    def update_cost(self, model: ModelType, token_usage: TokenUsage):
        """Update daily cost tracking"""
        today = datetime.utcnow().date()
        self.daily_costs[today] += token_usage.estimated_cost
        
        logger.info(f"Model: {model.value}, Cost: ${token_usage.estimated_cost:.4f}, "
                   f"Daily total: ${self.daily_costs[today]:.2f}")


class PromptOptimizer:
    """Optimize prompts for efficiency and effectiveness"""
    
    def __init__(self):
        self.prompt_templates = {}
        self.performance_metrics = defaultdict(list)
    
    def optimize_prompt(self, prompt: str, context_type: str = 'general') -> str:
        """Optimize prompt for token efficiency"""
        # Remove redundant whitespace
        prompt = ' '.join(prompt.split())
        
        # Compress common phrases
        replacements = {
            'Please analyze and provide': 'Analyze:',
            'Can you help me understand': 'Explain:',
            'I would like to know': 'Query:',
            'กรุณาวิเคราะห์และให้คำแนะนำ': 'วิเคราะห์:',
            'ช่วยอธิบายให้ฉันเข้าใจ': 'อธิบาย:',
        }
        
        for long_phrase, short_phrase in replacements.items():
            prompt = prompt.replace(long_phrase, short_phrase)
        
        return prompt
    
    def create_dynamic_prompt(self, base_prompt: str, variables: Dict[str, Any]) -> str:
        """Create dynamic prompt with variable injection"""
        # Sanitize variables
        safe_vars = {}
        for key, value in variables.items():
            if isinstance(value, str):
                safe_vars[key] = value[:500]  # Limit length
            else:
                safe_vars[key] = str(value)
        
        # Replace variables in prompt
        try:
            return base_prompt.format(**safe_vars)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            return base_prompt
    
    def get_optimized_system_prompt(self, context_type: str, user_context: Dict) -> str:
        """Get optimized system prompt for specific context"""
        base_prompts = {
            'conversation': """Thai SME advisor. Respond in user's language.
Focus: {focus_areas}
Context: {business_type}, {location}, {stage}
Be concise, practical, actionable.""",
            
            'image_analysis': """Analyze image for Thai SME context.
Focus: Business relevance, actionable insights.
Language: {language}""",
            
            'file_analysis': """Analyze document for Thai SME.
Type: {file_type}
Focus: Key insights, actions needed.
Language: {language}"""
        }
        
        # Get base prompt
        base = base_prompts.get(context_type, base_prompts['conversation'])
        
        # Prepare variables with defaults
        variables = {
            'focus_areas': user_context.get('focus_areas', 'general business advice'),
            'business_type': user_context.get('business_type', 'SME'),
            'location': user_context.get('location', 'Thailand'),
            'stage': user_context.get('stage', 'operating'),
            'language': user_context.get('language', 'th'),
            'file_type': user_context.get('file_type', 'document')
        }
        
        return self.create_dynamic_prompt(base, variables)


class AIOptimizationManager:
    """Main manager for AI optimization strategies"""
    
    def __init__(self):
        self.context_optimizer = ContextOptimizer()
        self.response_cache = ResponseCache(max_size=2000, ttl_hours=Config.CACHE_TTL_HOURS)
        self.request_optimizer = RequestOptimizer()
        self.model_selector = ModelSelector(cost_threshold_daily=Config.DAILY_COST_LIMIT)
        self.prompt_optimizer = PromptOptimizer()
        self.rate_limiter = AdvancedRateLimiter(
            requests_per_minute=Config.RATE_LIMIT_PER_MINUTE,
            tokens_per_minute=Config.TOKEN_BUDGET_PER_USER * 10  # Global token limit
        )
        
        # Performance tracking
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        # Metrics tracking
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'tokens_saved': 0,
            'requests_optimized': 0,
            'cost_saved': 0.0,
            'average_response_time': 0.0
        }
    
    def check_rate_limit_and_optimize(self, messages: List[Dict], user_context: Dict, 
                                     task_type: str = 'conversation') -> Tuple[bool, Dict]:
        """Check rate limits and optimize request if allowed"""
        # Estimate token usage for rate limiting
        estimated_tokens = sum(len(msg['content']) // 4 for msg in messages if msg.get('content'))
        estimated_tokens = max(estimated_tokens, 500)  # Minimum estimate
        
        # Check rate limits
        can_proceed, wait_time = self.rate_limiter.check_rate_limit(estimated_tokens)
        
        if not can_proceed:
            return False, {
                'error': 'rate_limited',
                'wait_time': wait_time,
                'message': f'Rate limit exceeded. Please wait {wait_time:.1f} seconds.',
                'circuit_state': self.rate_limiter.circuit_state
            }
        
        # Proceed with optimization
        optimization_result = self.optimize_request(messages, user_context, task_type)
        optimization_result['estimated_tokens'] = estimated_tokens
        
        return True, optimization_result
    
    def optimize_request(self, messages: List[Dict], user_context: Dict, 
                        task_type: str = 'conversation') -> Dict:
        """Optimize a request before sending to API"""
        optimization_result = {
            'messages': messages,
            'model': None,
            'max_tokens': 800,
            'temperature': 0.5,
            'cached_response': None,
            'optimization_applied': []
        }
        
        # Check cache first
        if messages:
            last_message = messages[-1]['content']
            cached = self.response_cache.get(last_message, user_context)
            if cached:
                self.metrics['cache_hits'] += 1
                optimization_result['cached_response'] = cached
                return optimization_result
            else:
                self.metrics['cache_misses'] += 1
        
        # Optimize context
        optimized_messages = self.context_optimizer.compress_context(
            messages, target_tokens=3000
        )
        optimization_result['messages'] = optimized_messages
        
        # Select optimal model
        complexity = self.model_selector.estimate_task_complexity(
            messages[-1]['content'] if messages else '',
            has_context=len(messages) > 1
        )
        selected_model = self.model_selector.select_model(
            task_type, complexity, user_context.get('tier', 'free')
        )
        optimization_result['model'] = selected_model.value
        
        # Optimize prompt
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] = self.prompt_optimizer.optimize_prompt(
                messages[0]['content'], task_type
            )
        
        # Set optimal parameters based on task
        if task_type == 'simple_greeting':
            optimization_result['max_tokens'] = 200
            optimization_result['temperature'] = 0.3
        elif task_type == 'document_analysis':
            optimization_result['max_tokens'] = 1000
            optimization_result['temperature'] = 0.4
        elif task_type == 'creative_writing':
            optimization_result['max_tokens'] = 800
            optimization_result['temperature'] = 0.7
        
        self.metrics['requests_optimized'] += 1
        return optimization_result
    
    def post_process_response(self, prompt: str, response: str, 
                            user_context: Dict, token_usage: TokenUsage):
        """Post-process response and update metrics"""
        start_time = time.time()
        
        # Cache the response
        self.response_cache.set(prompt, response, user_context)
        
        # Calculate response time
        response_time = time.time() - token_usage.timestamp if hasattr(token_usage, 'timestamp') else 1.0
        
        # Record request in rate limiter
        success = len(response) > 0 and 'error' not in response.lower()
        self.rate_limiter.record_request(token_usage.total_tokens, response_time, success)
        
        # Update model costs
        if hasattr(token_usage, 'model'):
            try:
                model_type = ModelType(token_usage.model)
                self.model_selector.update_cost(model_type, token_usage)
            except ValueError:
                logger.warning(f"Unknown model type: {token_usage.model}")
        
        # Update global metrics
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        self.total_tokens_used += token_usage.total_tokens
        self.total_cost += token_usage.estimated_cost
        
        # Update average response time
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (self.total_requests - 1) + response_time) / self.total_requests
        )
        
        # Track tokens and cost saved through optimization
        baseline_tokens = len(prompt) // 3  # Rough estimate of unoptimized tokens
        tokens_saved = max(0, baseline_tokens - token_usage.total_tokens)
        self.metrics['tokens_saved'] += tokens_saved
        
        # Estimate cost saved
        if tokens_saved > 0:
            # Assume GPT-4 pricing for cost saved calculation
            cost_saved = (tokens_saved / 1000) * 0.03  # $0.03 per 1K tokens
            self.metrics['cost_saved'] += cost_saved
    
    def get_metrics_summary(self) -> Dict:
        """Get optimization metrics summary"""
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_rate = self.metrics['cache_hits'] / cache_total if cache_total > 0 else 0
        
        return {
            'cache_hit_rate': f"{cache_rate:.2%}",
            'tokens_saved': self.metrics['tokens_saved'],
            'requests_optimized': self.metrics['requests_optimized'],
            'daily_cost': f"${sum(self.model_selector.daily_costs.values()):.2f}",
            'cost_saved': f"${self.metrics['cost_saved']:.3f}",
            'success_rate': f"{(self.successful_requests / max(1, self.total_requests)) * 100:.1f}%"
        }
    
    def get_optimization_metrics(self) -> Dict:
        """Get comprehensive optimization metrics"""
        uptime_hours = (time.time() - self.start_time) / 3600
        success_rate = (self.successful_requests / max(1, self.total_requests)) * 100
        
        # Cache metrics
        cache_stats = self.response_cache.get_cache_stats()
        
        # Rate limiter metrics
        rate_limit_stats = self.rate_limiter.get_metrics()
        
        return {
            'performance': {
                'uptime_hours': round(uptime_hours, 2),
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'success_rate_percent': round(success_rate, 2),
                'average_response_time_ms': round(self.metrics['average_response_time'] * 1000, 1),
                'requests_per_hour': round(self.total_requests / max(0.1, uptime_hours), 1)
            },
            'caching': cache_stats,
            'rate_limiting': rate_limit_stats,
            'cost_optimization': {
                'total_tokens_used': self.total_tokens_used,
                'tokens_saved': self.metrics['tokens_saved'],
                'total_cost': round(self.total_cost, 4),
                'cost_saved': round(self.metrics['cost_saved'], 4),
                'cost_per_request': round(self.total_cost / max(1, self.total_requests), 4),
                'daily_cost': round(sum(self.model_selector.daily_costs.values()), 2),
                'cost_efficiency_percent': round((self.metrics['cost_saved'] / max(0.01, self.total_cost)) * 100, 1)
            },
            'optimization_stats': {
                'requests_optimized': self.metrics['requests_optimized'],
                'context_compressions': 0,  # TODO: Track this
                'model_selections': len(set(self.model_selector.task_patterns.values())),
                'prompt_optimizations': 0  # TODO: Track this
            }
        }
    
    def clear_metrics(self):
        """Reset all metrics (useful for testing or periodic resets)"""
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'tokens_saved': 0,
            'requests_optimized': 0,
            'cost_saved': 0.0,
            'average_response_time': 0.0
        }
        self.total_requests = 0
        self.successful_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.start_time = time.time()
        
        # Clear cache metrics
        self.response_cache.hit_count = 0
        self.response_cache.miss_count = 0
        
        logger.info("AI optimization metrics cleared")


# Singleton instance
ai_optimizer = AIOptimizationManager()