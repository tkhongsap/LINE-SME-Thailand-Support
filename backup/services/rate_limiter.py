import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from threading import Lock
from datetime import datetime, timedelta

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls and user messages"""
    
    def __init__(self):
        self.user_buckets = defaultdict(lambda: TokenBucket(
            capacity=Config.RATE_LIMIT_PER_USER,
            refill_rate=Config.RATE_LIMIT_PER_USER / Config.RATE_LIMIT_WINDOW
        ))
        self.api_bucket = TokenBucket(
            capacity=Config.API_RATE_LIMIT,
            refill_rate=Config.API_RATE_LIMIT / 60  # per minute
        )
        self.user_message_history = defaultdict(deque)
        self.lock = Lock()
    
    def check_user_rate_limit(self, user_id: str) -> Tuple[bool, Optional[float]]:
        """Check if user has available tokens"""
        with self.lock:
            bucket = self.user_buckets[user_id]
            allowed = bucket.consume(1)
            
            if not allowed:
                # Calculate wait time
                wait_time = bucket.time_until_refill()
                logger.warning(f"User {user_id} rate limited. Wait {wait_time:.1f}s")
                return False, wait_time
            
            # Track message timestamp
            self.user_message_history[user_id].append(time.time())
            self._cleanup_old_history(user_id)
            
            return True, None
    
    def check_api_rate_limit(self) -> Tuple[bool, Optional[float]]:
        """Check if API calls are within limits"""
        with self.lock:
            allowed = self.api_bucket.consume(1)
            
            if not allowed:
                wait_time = self.api_bucket.time_until_refill()
                logger.warning(f"API rate limited. Wait {wait_time:.1f}s")
                return False, wait_time
            
            return True, None
    
    def get_user_usage_stats(self, user_id: str) -> Dict:
        """Get usage statistics for a user"""
        with self.lock:
            bucket = self.user_buckets[user_id]
            history = self.user_message_history[user_id]
            
            # Calculate messages in last minute
            current_time = time.time()
            recent_messages = sum(1 for ts in history if current_time - ts < 60)
            
            return {
                'available_tokens': bucket.tokens,
                'capacity': bucket.capacity,
                'recent_messages': recent_messages,
                'rate_limit': Config.RATE_LIMIT_PER_USER,
                'window_seconds': Config.RATE_LIMIT_WINDOW
            }
    
    def _cleanup_old_history(self, user_id: str):
        """Remove old message timestamps"""
        current_time = time.time()
        history = self.user_message_history[user_id]
        
        # Remove timestamps older than rate limit window
        while history and current_time - history[0] > Config.RATE_LIMIT_WINDOW:
            history.popleft()


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - self.last_refill
        
        # Add tokens based on refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = current_time
    
    def time_until_refill(self, tokens: int = 1) -> float:
        """Calculate time until enough tokens are available"""
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class CircuitBreaker:
    """Circuit breaker pattern for handling API failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        self.lock = Lock()
    
    def record_success(self):
        """Record successful API call"""
        with self.lock:
            self.failure_count = 0
            self.state = 'closed'
    
    def record_failure(self):
        """Record failed API call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_proceed(self) -> bool:
        """Check if circuit breaker allows the call"""
        with self.lock:
            if self.state == 'closed':
                return True
            
            if self.state == 'open':
                # Check if recovery timeout has passed
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'half-open'
                    logger.info("Circuit breaker entering half-open state")
                    return True
                return False
            
            # half-open state
            return True
    
    def get_state(self) -> Dict:
        """Get circuit breaker state"""
        with self.lock:
            return {
                'state': self.state,
                'failure_count': self.failure_count,
                'threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout,
                'last_failure': self.last_failure_time
            }


class ExponentialBackoff:
    """Exponential backoff for retry logic"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.base_delay * (self.factor ** attempt)
        return min(delay, self.max_delay)
    
    def get_jittered_delay(self, attempt: int) -> float:
        """Get delay with random jitter to prevent thundering herd"""
        import random
        delay = self.get_delay(attempt)
        # Add 0-25% random jitter
        jitter = delay * random.uniform(0, 0.25)
        return delay + jitter


# Global instances
rate_limiter = RateLimiter()
line_api_circuit_breaker = CircuitBreaker()
backoff_calculator = ExponentialBackoff()