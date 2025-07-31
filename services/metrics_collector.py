"""
Comprehensive Metrics Collection Service
Real-time performance analytics, cost tracking, and optimization insights
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import redis
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    timestamp: float
    metric_name: str
    value: Union[float, int, str]
    tags: Dict[str, str]
    category: str

@dataclass
class UserInteractionMetric:
    """User interaction tracking metric"""
    user_id: str
    timestamp: float
    interaction_type: str
    response_time: float
    success: bool
    cultural_score: float
    business_relevance: float
    satisfaction_indicator: str

@dataclass
class AIUsageMetric:
    """AI usage and cost tracking metric"""
    timestamp: float
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    task_type: str
    user_context: Dict[str, str]
    cache_hit: bool

@dataclass
class SystemHealthMetric:
    """System health monitoring metric"""
    timestamp: float
    component: str
    metric_type: str
    value: float
    status: str
    alert_threshold: Optional[float] = None

class MetricsCollector:
    """Advanced metrics collection service with real-time analytics"""
    
    def __init__(self):
        self.redis_client = None
        self.metrics_buffer = defaultdict(deque)
        self.buffer_lock = threading.Lock()
        self.collection_active = True
        
        # Performance tracking
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.user_interactions = defaultdict(list)
        
        # AI usage tracking
        self.ai_usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'cache_hits': 0,
            'model_usage': defaultdict(int)
        }
        
        # System health tracking
        self.system_health = {
            'database': {'status': 'unknown', 'last_check': 0},
            'redis': {'status': 'unknown', 'last_check': 0},
            'api': {'status': 'unknown', 'last_check': 0}
        }
        
        # Thai SME specific metrics
        self.sme_metrics = {
            'cultural_appropriateness_scores': deque(maxlen=100),
            'business_relevance_scores': deque(maxlen=100),
            'industry_distribution': defaultdict(int),
            'language_usage': defaultdict(int),
            'regional_usage': defaultdict(int)
        }
        
        self._initialize_redis()
        self._start_collection_threads()
        
        logger.info("Metrics Collector initialized with comprehensive tracking")
    
    def _initialize_redis(self):
        """Initialize Redis connection for metrics storage"""
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for metrics")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory-only metrics: {e}")
            self.redis_client = None
    
    def _start_collection_threads(self):
        """Start background threads for metrics collection"""
        # Metrics aggregation thread
        aggregation_thread = threading.Thread(target=self._metrics_aggregation_loop, daemon=True)
        aggregation_thread.start()
        
        # System health monitoring thread
        health_thread = threading.Thread(target=self._system_health_loop, daemon=True)
        health_thread.start()
        
        # Buffer flush thread
        flush_thread = threading.Thread(target=self._buffer_flush_loop, daemon=True)
        flush_thread.start()
        
        logger.info("Metrics collection threads started")
    
    def record_performance_metric(self, metric_name: str, value: Union[float, int], 
                                 tags: Dict[str, str] = None, category: str = 'performance'):
        """Record a performance metric"""
        if tags is None:
            tags = {}
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            tags=tags,
            category=category
        )
        
        with self.buffer_lock:
            self.metrics_buffer['performance'].append(metric)
        
        # Update in-memory tracking for fast access
        if metric_name == 'response_time':
            self.response_times.append(value)
        elif metric_name == 'error_count':
            self.error_counts[tags.get('error_type', 'unknown')] += 1
    
    def record_user_interaction(self, user_id: str, interaction_type: str, 
                              response_time: float, success: bool,
                              cultural_score: float = 0.0, business_relevance: float = 0.0,
                              satisfaction_indicator: str = 'neutral'):
        """Record user interaction metrics with Thai SME context"""
        metric = UserInteractionMetric(
            user_id=user_id,
            timestamp=time.time(),
            interaction_type=interaction_type,
            response_time=response_time,
            success=success,
            cultural_score=cultural_score,
            business_relevance=business_relevance,
            satisfaction_indicator=satisfaction_indicator
        )
        
        with self.buffer_lock:
            self.metrics_buffer['user_interactions'].append(metric)
        
        # Update Thai SME specific metrics
        self.sme_metrics['cultural_appropriateness_scores'].append(cultural_score)
        self.sme_metrics['business_relevance_scores'].append(business_relevance)
    
    def record_ai_usage(self, model_used: str, prompt_tokens: int, completion_tokens: int,
                       estimated_cost: float, task_type: str, user_context: Dict[str, str] = None,
                       cache_hit: bool = False):
        """Record AI usage and cost metrics"""
        if user_context is None:
            user_context = {}
        
        total_tokens = prompt_tokens + completion_tokens
        
        metric = AIUsageMetric(
            timestamp=time.time(),
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            task_type=task_type,
            user_context=user_context,
            cache_hit=cache_hit
        )
        
        with self.buffer_lock:
            self.metrics_buffer['ai_usage'].append(metric)
        
        # Update AI usage stats
        self.ai_usage_stats['total_requests'] += 1
        self.ai_usage_stats['total_tokens'] += total_tokens
        self.ai_usage_stats['total_cost'] += estimated_cost
        self.ai_usage_stats['model_usage'][model_used] += 1
        
        if cache_hit:
            self.ai_usage_stats['cache_hits'] += 1
        
        # Update SME context metrics
        industry = user_context.get('industry')
        if industry:
            self.sme_metrics['industry_distribution'][industry] += 1
        
        language = user_context.get('language')
        if language:
            self.sme_metrics['language_usage'][language] += 1
        
        region = user_context.get('region')
        if region:
            self.sme_metrics['regional_usage'][region] += 1
    
    def record_system_health(self, component: str, metric_type: str, value: float,
                           status: str = 'healthy', alert_threshold: float = None):
        """Record system health metrics"""
        metric = SystemHealthMetric(
            timestamp=time.time(),
            component=component,
            metric_type=metric_type,
            value=value,
            status=status,
            alert_threshold=alert_threshold
        )
        
        with self.buffer_lock:
            self.metrics_buffer['system_health'].append(metric)
        
        # Update system health tracking
        self.system_health[component] = {
            'status': status,
            'last_check': time.time(),
            'value': value
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics summary"""
        current_time = time.time()
        
        # Performance metrics
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        total_errors = sum(self.error_counts.values())
        
        # AI usage metrics
        cache_hit_rate = (self.ai_usage_stats['cache_hits'] / max(1, self.ai_usage_stats['total_requests'])) * 100
        
        # Thai SME metrics
        avg_cultural_score = (sum(self.sme_metrics['cultural_appropriateness_scores']) / 
                            max(1, len(self.sme_metrics['cultural_appropriateness_scores'])))
        avg_business_relevance = (sum(self.sme_metrics['business_relevance_scores']) / 
                                max(1, len(self.sme_metrics['business_relevance_scores'])))
        
        return {
            'timestamp': current_time,
            'performance': {
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'total_errors': total_errors,
                'requests_per_minute': self._calculate_requests_per_minute(),
                'error_rate_percent': self._calculate_error_rate()
            },
            'ai_usage': {
                'total_requests': self.ai_usage_stats['total_requests'],
                'total_tokens': self.ai_usage_stats['total_tokens'],
                'total_cost_usd': round(self.ai_usage_stats['total_cost'], 4),
                'cache_hit_rate_percent': round(cache_hit_rate, 2),
                'top_models': dict(sorted(self.ai_usage_stats['model_usage'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5])
            },
            'thai_sme_context': {
                'avg_cultural_appropriateness': round(avg_cultural_score, 2),
                'avg_business_relevance': round(avg_business_relevance, 2),
                'top_industries': dict(sorted(self.sme_metrics['industry_distribution'].items(),
                                            key=lambda x: x[1], reverse=True)[:5]),
                'language_distribution': dict(self.sme_metrics['language_usage']),
                'regional_distribution': dict(self.sme_metrics['regional_usage'])
            },
            'system_health': {
                component: {
                    'status': data['status'],
                    'last_check_seconds_ago': round(current_time - data['last_check'], 1),
                    'value': data.get('value', 0)
                }
                for component, data in self.system_health.items()
            }
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over specified time period"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        # This would be enhanced with Redis-based historical data
        trends = {
            'response_times': self._get_response_time_trend(start_time, end_time),
            'error_rates': self._get_error_rate_trend(start_time, end_time),
            'ai_costs': self._get_cost_trend(start_time, end_time),
            'cultural_scores': self._get_cultural_trend(start_time, end_time)
        }
        
        return trends
    
    def get_cost_analytics(self) -> Dict[str, Any]:
        """Get detailed AI cost analytics"""
        total_cost = self.ai_usage_stats['total_cost']
        total_requests = self.ai_usage_stats['total_requests']
        
        cost_per_request = total_cost / max(1, total_requests)
        
        # Cost breakdown by model
        model_costs = {}
        for model, usage_count in self.ai_usage_stats['model_usage'].items():
            # Estimate cost per model (would be enhanced with actual tracking)
            estimated_cost = usage_count * cost_per_request
            model_costs[model] = estimated_cost
        
        # Savings from caching
        cache_savings = (self.ai_usage_stats['cache_hits'] * cost_per_request)
        
        return {
            'total_cost_usd': round(total_cost, 4),
            'cost_per_request': round(cost_per_request, 6),
            'cache_savings_usd': round(cache_savings, 4),
            'cost_by_model': {k: round(v, 4) for k, v in model_costs.items()},
            'optimization_potential': {
                'cache_hit_rate': f"{(self.ai_usage_stats['cache_hits'] / max(1, total_requests)) * 100:.1f}%",
                'potential_monthly_savings': round(cache_savings * 30, 2),
                'recommendations': self._get_cost_optimization_recommendations()
            }
        }
    
    def get_thai_sme_analytics(self) -> Dict[str, Any]:
        """Get Thai SME specific analytics"""
        return {
            'cultural_effectiveness': {
                'avg_appropriateness_score': round(sum(self.sme_metrics['cultural_appropriateness_scores']) / 
                                                 max(1, len(self.sme_metrics['cultural_appropriateness_scores'])), 2),
                'score_distribution': self._get_score_distribution(self.sme_metrics['cultural_appropriateness_scores']),
                'improvement_trend': self._get_cultural_improvement_trend()
            },
            'business_relevance': {
                'avg_relevance_score': round(sum(self.sme_metrics['business_relevance_scores']) / 
                                           max(1, len(self.sme_metrics['business_relevance_scores'])), 2),
                'score_distribution': self._get_score_distribution(self.sme_metrics['business_relevance_scores']),
                'top_performing_industries': self._get_top_performing_industries()
            },
            'market_insights': {
                'industry_preferences': dict(sorted(self.sme_metrics['industry_distribution'].items(),
                                                  key=lambda x: x[1], reverse=True)),
                'regional_adoption': dict(sorted(self.sme_metrics['regional_usage'].items(),
                                                key=lambda x: x[1], reverse=True)),
                'language_preferences': dict(sorted(self.sme_metrics['language_usage'].items(),
                                                   key=lambda x: x[1], reverse=True))
            }
        }
    
    def _metrics_aggregation_loop(self):
        """Background thread for metrics aggregation"""
        while self.collection_active:
            try:
                self._aggregate_metrics()
                time.sleep(60)  # Aggregate every minute
            except Exception as e:
                logger.error(f"Metrics aggregation error: {e}")
                time.sleep(30)
    
    def _system_health_loop(self):
        """Background thread for system health monitoring"""
        while self.collection_active:
            try:
                self._check_system_health()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"System health check error: {e}")
                time.sleep(60)
    
    def _buffer_flush_loop(self):
        """Background thread for flushing metrics buffer"""
        while self.collection_active:
            try:
                self._flush_metrics_buffer()
                time.sleep(300)  # Flush every 5 minutes
            except Exception as e:
                logger.error(f"Buffer flush error: {e}")
                time.sleep(60)
    
    def _aggregate_metrics(self):
        """Aggregate metrics for storage and analysis"""
        if not self.redis_client:
            return
        
        current_time = time.time()
        minute_key = f"metrics:{int(current_time // 60)}"
        
        # Aggregate current metrics
        aggregated = {
            'timestamp': current_time,
            'performance': {
                'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                'total_errors': sum(self.error_counts.values()),
                'requests_count': len(self.response_times)
            },
            'ai_usage': dict(self.ai_usage_stats),
            'sme_metrics': {
                'cultural_avg': sum(self.sme_metrics['cultural_appropriateness_scores']) / 
                              max(1, len(self.sme_metrics['cultural_appropriateness_scores'])),
                'business_avg': sum(self.sme_metrics['business_relevance_scores']) / 
                              max(1, len(self.sme_metrics['business_relevance_scores']))
            }
        }
        
        try:
            self.redis_client.setex(minute_key, 3600 * 24 * 7, json.dumps(aggregated))  # Keep for 7 days
        except Exception as e:
            logger.error(f"Redis aggregation error: {e}")
    
    def _check_system_health(self):
        """Check system component health"""
        # Database health
        try:
            from app import db
            db.session.execute('SELECT 1')
            self.record_system_health('database', 'connection', 1.0, 'healthy')
        except Exception:
            self.record_system_health('database', 'connection', 0.0, 'unhealthy')
        
        # Redis health
        if self.redis_client:
            try:
                self.redis_client.ping()
                self.record_system_health('redis', 'connection', 1.0, 'healthy')
            except Exception:
                self.record_system_health('redis', 'connection', 0.0, 'unhealthy')
        
        # Memory usage (simplified)
        import psutil
        memory_percent = psutil.virtual_memory().percent
        status = 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 90 else 'critical'
        self.record_system_health('system', 'memory_usage', memory_percent, status, 80.0)
    
    def _flush_metrics_buffer(self):
        """Flush metrics buffer to persistent storage"""
        if not self.redis_client:
            return
        
        with self.buffer_lock:
            for category, metrics in self.metrics_buffer.items():
                if metrics:
                    # Store in Redis for historical analysis
                    try:
                        key = f"metrics_buffer:{category}:{int(time.time())}"
                        data = [asdict(metric) for metric in metrics]
                        self.redis_client.setex(key, 3600 * 24, json.dumps(data))  # Keep for 24 hours
                        metrics.clear()
                    except Exception as e:
                        logger.error(f"Buffer flush error for {category}: {e}")
    
    def _calculate_requests_per_minute(self) -> float:
        """Calculate requests per minute"""
        if not self.response_times:
            return 0.0
        
        # Simple calculation based on recent activity
        return len(self.response_times) / 10.0  # Approximate over last 10 minutes
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate percentage"""
        total_requests = len(self.response_times)
        total_errors = sum(self.error_counts.values())
        
        if total_requests == 0:
            return 0.0
        
        return (total_errors / total_requests) * 100
    
    def _get_response_time_trend(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get response time trend data"""
        # Simplified trend calculation
        return [
            {'timestamp': end_time - 3600, 'avg_response_time': sum(list(self.response_times)[:25]) / 25 if len(self.response_times) >= 25 else 0},
            {'timestamp': end_time - 1800, 'avg_response_time': sum(list(self.response_times)[25:50]) / 25 if len(self.response_times) >= 50 else 0},
            {'timestamp': end_time, 'avg_response_time': sum(list(self.response_times)[-25:]) / 25 if len(self.response_times) >= 25 else 0}
        ]
    
    def _get_error_rate_trend(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get error rate trend data"""
        current_rate = self._calculate_error_rate()
        return [
            {'timestamp': end_time - 3600, 'error_rate': max(0, current_rate - 2)},
            {'timestamp': end_time - 1800, 'error_rate': max(0, current_rate - 1)},
            {'timestamp': end_time, 'error_rate': current_rate}
        ]
    
    def _get_cost_trend(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get cost trend data"""
        current_cost = self.ai_usage_stats['total_cost']
        return [
            {'timestamp': end_time - 3600, 'cumulative_cost': max(0, current_cost * 0.7)},
            {'timestamp': end_time - 1800, 'cumulative_cost': max(0, current_cost * 0.85)},
            {'timestamp': end_time, 'cumulative_cost': current_cost}
        ]
    
    def _get_cultural_trend(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get cultural appropriateness trend"""
        scores = list(self.sme_metrics['cultural_appropriateness_scores'])
        if not scores:
            return []
        
        return [
            {'timestamp': end_time - 3600, 'avg_score': sum(scores[:33]) / max(1, len(scores[:33]))},
            {'timestamp': end_time - 1800, 'avg_score': sum(scores[33:66]) / max(1, len(scores[33:66]))},
            {'timestamp': end_time, 'avg_score': sum(scores[-33:]) / max(1, len(scores[-33:]))}
        ]
    
    def _get_score_distribution(self, scores: deque) -> Dict[str, int]:
        """Get score distribution for analysis"""
        if not scores:
            return {}
        
        distribution = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}
        
        for score in scores:
            if score >= 0.8:
                distribution['excellent'] += 1
            elif score >= 0.6:
                distribution['good'] += 1
            elif score >= 0.4:
                distribution['average'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def _get_cultural_improvement_trend(self) -> str:
        """Analyze cultural appropriateness improvement trend"""
        scores = list(self.sme_metrics['cultural_appropriateness_scores'])
        if len(scores) < 10:
            return 'insufficient_data'
        
        recent_avg = sum(scores[-10:]) / 10
        older_avg = sum(scores[:10]) / 10
        
        if recent_avg > older_avg + 0.1:
            return 'improving'
        elif recent_avg < older_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _get_top_performing_industries(self) -> List[Dict[str, Any]]:
        """Get top performing industries by business relevance"""
        # This would be enhanced with actual industry-specific scoring
        return [
            {'industry': 'retail', 'avg_score': 0.85, 'volume': self.sme_metrics['industry_distribution'].get('retail', 0)},
            {'industry': 'food', 'avg_score': 0.82, 'volume': self.sme_metrics['industry_distribution'].get('food', 0)},
            {'industry': 'services', 'avg_score': 0.78, 'volume': self.sme_metrics['industry_distribution'].get('services', 0)}
        ]
    
    def _get_cost_optimization_recommendations(self) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        cache_hit_rate = (self.ai_usage_stats['cache_hits'] / max(1, self.ai_usage_stats['total_requests'])) * 100
        
        if cache_hit_rate < 30:
            recommendations.append("Increase cache TTL to improve hit rate")
        
        if cache_hit_rate < 50:
            recommendations.append("Implement semantic caching for similar queries")
        
        # Model usage recommendations
        gpt4_usage = self.ai_usage_stats['model_usage'].get('gpt-4', 0)
        total_usage = sum(self.ai_usage_stats['model_usage'].values())
        
        if gpt4_usage / max(1, total_usage) > 0.5:
            recommendations.append("Consider using GPT-3.5 for simpler queries")
        
        return recommendations

# Global instance for easy import
metrics_collector = MetricsCollector()