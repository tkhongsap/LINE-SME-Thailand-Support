"""
Advanced Performance Monitoring Service
Real-time monitoring with intelligent alerting and anomaly detection
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config
from services.metrics_collector import metrics_collector

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Alert configuration and status"""
    alert_id: str
    name: str
    condition: str
    threshold: float
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True
    last_triggered: float = 0
    trigger_count: int = 0
    cooldown_minutes: int = 30

@dataclass
class AlertEvent:
    """Alert event occurrence"""
    alert_id: str
    timestamp: float
    severity: str
    message: str
    current_value: float
    threshold: float
    context: Dict[str, Any]

class MonitoringService:
    """Advanced monitoring service with intelligent alerting"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.monitoring_active = True
        self.alert_handlers: List[Callable] = []
        
        # Performance tracking
        self.performance_trends = {
            'response_times': deque(maxlen=100),
            'error_rates': deque(maxlen=100),
            'throughput': deque(maxlen=100),
            'cost_per_hour': deque(maxlen=24)
        }
        
        # Anomaly detection
        self.baseline_metrics = {}
        self.anomaly_threshold = 2.0  # Standard deviations
        
        # System health tracking
        self.health_status = {
            'overall': 'healthy',
            'database': 'unknown',
            'redis': 'unknown',
            'api': 'unknown',
            'ai_service': 'unknown'
        }
        
        # Thai SME specific monitoring
        self.sme_performance = {
            'cultural_effectiveness': deque(maxlen=50),
            'business_relevance': deque(maxlen=50),
            'user_satisfaction': deque(maxlen=50)
        }
        
        self._setup_default_alerts()
        self._start_monitoring_threads()
        
        logger.info("Monitoring Service initialized with intelligent alerting")
    
    def _setup_default_alerts(self):
        """Setup default monitoring alerts"""
        default_alerts = [
            Alert(
                alert_id="high_response_time",
                name="High Response Time",
                condition="avg_response_time > threshold",
                threshold=3000.0,  # 3 seconds
                severity="warning"
            ),
            Alert(
                alert_id="critical_response_time",
                name="Critical Response Time",
                condition="avg_response_time > threshold",
                threshold=5000.0,  # 5 seconds
                severity="critical"
            ),
            Alert(
                alert_id="high_error_rate",
                name="High Error Rate",
                condition="error_rate > threshold",
                threshold=10.0,  # 10%
                severity="warning"
            ),
            Alert(
                alert_id="critical_error_rate",
                name="Critical Error Rate",
                condition="error_rate > threshold",
                threshold=25.0,  # 25%
                severity="critical"
            ),
            Alert(
                alert_id="high_ai_cost",
                name="High AI Usage Cost",
                condition="hourly_cost > threshold",
                threshold=5.0,  # $5 per hour
                severity="warning"
            ),
            Alert(
                alert_id="low_cultural_score",
                name="Low Cultural Appropriateness",
                condition="cultural_score < threshold",
                threshold=0.6,  # 60%
                severity="warning"
            ),
            Alert(
                alert_id="database_unhealthy",
                name="Database Connection Issues",
                condition="database_status == 'unhealthy'",
                threshold=1.0,
                severity="critical"
            ),
            Alert(
                alert_id="cache_hit_rate_low",
                name="Low Cache Hit Rate",
                condition="cache_hit_rate < threshold",
                threshold=30.0,  # 30%
                severity="info"
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.alert_id] = alert
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        # Main monitoring loop
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        # Performance trend analysis
        trend_thread = threading.Thread(target=self._trend_analysis_loop, daemon=True)
        trend_thread.start()
        
        # Anomaly detection
        anomaly_thread = threading.Thread(target=self._anomaly_detection_loop, daemon=True)
        anomaly_thread.start()
        
        # SLA monitoring
        sla_thread = threading.Thread(target=self._sla_monitoring_loop, daemon=True)
        sla_thread.start()
        
        logger.info("Monitoring threads started")
    
    def _monitoring_loop(self):
        """Main monitoring loop - checks alerts every 30 seconds"""
        while self.monitoring_active:
            try:
                self._check_all_alerts()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)
    
    def _trend_analysis_loop(self):
        """Analyze performance trends every 5 minutes"""
        while self.monitoring_active:
            try:
                self._analyze_performance_trends()
                time.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")
                time.sleep(600)  # 10 minutes on error
    
    def _anomaly_detection_loop(self):
        """Detect anomalies every 2 minutes"""
        while self.monitoring_active:
            try:
                self._detect_anomalies()
                time.sleep(120)  # 2 minutes
            except Exception as e:
                logger.error(f"Anomaly detection error: {e}")
                time.sleep(300)  # 5 minutes on error
    
    def _sla_monitoring_loop(self):
        """Monitor SLA compliance every 10 minutes"""
        while self.monitoring_active:
            try:
                self._monitor_sla_compliance()
                time.sleep(600)  # 10 minutes
            except Exception as e:
                logger.error(f"SLA monitoring error: {e}")
                time.sleep(900)  # 15 minutes on error
    
    def _check_all_alerts(self):
        """Check all configured alerts"""
        current_metrics = metrics_collector.get_real_time_metrics()
        current_time = time.time()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Check cooldown period
            if current_time - alert.last_triggered < (alert.cooldown_minutes * 60):
                continue
            
            # Evaluate alert condition
            should_trigger = self._evaluate_alert_condition(alert, current_metrics)
            
            if should_trigger:
                self._trigger_alert(alert, current_metrics)
    
    def _evaluate_alert_condition(self, alert: Alert, metrics: Dict[str, Any]) -> bool:
        """Evaluate if alert condition is met"""
        try:
            if alert.alert_id == "high_response_time" or alert.alert_id == "critical_response_time":
                return metrics['performance']['avg_response_time_ms'] > alert.threshold
            
            elif alert.alert_id == "high_error_rate" or alert.alert_id == "critical_error_rate":
                return metrics['performance']['error_rate_percent'] > alert.threshold
            
            elif alert.alert_id == "high_ai_cost":
                # Calculate hourly cost based on current rate
                total_cost = metrics['ai_usage']['total_cost_usd']
                # Estimate hourly rate (simplified)
                hourly_rate = total_cost * 4  # Rough estimate
                return hourly_rate > alert.threshold
            
            elif alert.alert_id == "low_cultural_score":
                return metrics['thai_sme_context']['avg_cultural_appropriateness'] < alert.threshold
            
            elif alert.alert_id == "database_unhealthy":
                return metrics['system_health']['database']['status'] != 'healthy'
            
            elif alert.alert_id == "cache_hit_rate_low":
                return metrics['ai_usage']['cache_hit_rate_percent'] < alert.threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert {alert.alert_id}: {e}")
            return False
    
    def _trigger_alert(self, alert: Alert, metrics: Dict[str, Any]):
        """Trigger an alert"""
        current_time = time.time()
        
        # Get current value for the alert
        current_value = self._get_current_value_for_alert(alert, metrics)
        
        # Create alert event
        alert_event = AlertEvent(
            alert_id=alert.alert_id,
            timestamp=current_time,
            severity=alert.severity,
            message=f"{alert.name}: {alert.condition} (Current: {current_value}, Threshold: {alert.threshold})",
            current_value=current_value,
            threshold=alert.threshold,
            context=metrics
        )
        
        # Update alert status
        alert.last_triggered = current_time
        alert.trigger_count += 1
        
        # Add to history
        self.alert_history.append(alert_event)
        
        # Log alert
        logger.warning(f"ALERT TRIGGERED: {alert_event.message}")
        
        # Notify handlers
        self._notify_alert_handlers(alert_event)
        
        # Update overall health status
        self._update_health_status(alert.severity)
    
    def _get_current_value_for_alert(self, alert: Alert, metrics: Dict[str, Any]) -> float:
        """Get current metric value for alert"""
        try:
            if "response_time" in alert.alert_id:
                return metrics['performance']['avg_response_time_ms']
            elif "error_rate" in alert.alert_id:
                return metrics['performance']['error_rate_percent']
            elif "ai_cost" in alert.alert_id:
                return metrics['ai_usage']['total_cost_usd'] * 4  # Hourly estimate
            elif "cultural_score" in alert.alert_id:
                return metrics['thai_sme_context']['avg_cultural_appropriateness']
            elif "cache_hit_rate" in alert.alert_id:
                return metrics['ai_usage']['cache_hit_rate_percent']
            else:
                return 0.0
        except:
            return 0.0
    
    def _notify_alert_handlers(self, alert_event: AlertEvent):
        """Notify all registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert_event)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def _update_health_status(self, severity: str):
        """Update overall system health based on alert severity"""
        if severity == "critical":
            self.health_status['overall'] = 'critical'
        elif severity == "warning" and self.health_status['overall'] == 'healthy':
            self.health_status['overall'] = 'warning'
    
    def _analyze_performance_trends(self):
        """Analyze performance trends and predict issues"""
        current_metrics = metrics_collector.get_real_time_metrics()
        
        # Track performance trends
        self.performance_trends['response_times'].append(
            current_metrics['performance']['avg_response_time_ms']
        )
        self.performance_trends['error_rates'].append(
            current_metrics['performance']['error_rate_percent']
        )
        self.performance_trends['throughput'].append(
            current_metrics['performance']['requests_per_minute']
        )
        
        # Calculate hourly cost and track
        hourly_cost = current_metrics['ai_usage']['total_cost_usd'] * 4
        self.performance_trends['cost_per_hour'].append(hourly_cost)
        
        # Detect trends
        trends = self._calculate_trends()
        
        # Generate predictive alerts
        self._generate_predictive_alerts(trends)
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calculate trend directions for key metrics"""
        trends = {}
        
        for metric_name, values in self.performance_trends.items():
            if len(values) >= 10:
                recent = list(values)[-5:]
                older = list(values)[-10:-5]
                
                recent_avg = sum(recent) / len(recent)
                older_avg = sum(older) / len(older)
                
                if recent_avg > older_avg * 1.2:
                    trends[metric_name] = 'increasing'
                elif recent_avg < older_avg * 0.8:
                    trends[metric_name] = 'decreasing'
                else:
                    trends[metric_name] = 'stable'
            else:
                trends[metric_name] = 'insufficient_data'
        
        return trends
    
    def _generate_predictive_alerts(self, trends: Dict[str, str]):
        """Generate predictive alerts based on trends"""
        if trends.get('response_times') == 'increasing':
            logger.info("PREDICTIVE ALERT: Response time trend increasing - consider optimization")
        
        if trends.get('cost_per_hour') == 'increasing':
            logger.info("PREDICTIVE ALERT: Cost trend increasing - review AI usage patterns")
        
        if trends.get('error_rates') == 'increasing':
            logger.warning("PREDICTIVE ALERT: Error rate trend increasing - investigate issues")
    
    def _detect_anomalies(self):
        """Detect anomalies using statistical analysis"""
        current_metrics = metrics_collector.get_real_time_metrics()
        
        # Update baseline metrics
        self._update_baseline_metrics(current_metrics)
        
        # Check for anomalies
        anomalies = self._find_statistical_anomalies(current_metrics)
        
        # Log significant anomalies
        for anomaly in anomalies:
            logger.warning(f"ANOMALY DETECTED: {anomaly}")
    
    def _update_baseline_metrics(self, current_metrics: Dict[str, Any]):
        """Update baseline metrics for anomaly detection"""
        key_metrics = [
            ('response_time', current_metrics['performance']['avg_response_time_ms']),
            ('error_rate', current_metrics['performance']['error_rate_percent']),
            ('cultural_score', current_metrics['thai_sme_context']['avg_cultural_appropriateness'])
        ]
        
        for metric_name, value in key_metrics:
            if metric_name not in self.baseline_metrics:
                self.baseline_metrics[metric_name] = {'values': deque(maxlen=100), 'mean': 0, 'std': 0}
            
            self.baseline_metrics[metric_name]['values'].append(value)
            
            # Recalculate statistics
            values = list(self.baseline_metrics[metric_name]['values'])
            if len(values) >= 10:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std = variance ** 0.5
                
                self.baseline_metrics[metric_name]['mean'] = mean
                self.baseline_metrics[metric_name]['std'] = std
    
    def _find_statistical_anomalies(self, current_metrics: Dict[str, Any]) -> List[str]:
        """Find statistical anomalies in current metrics"""
        anomalies = []
        
        current_values = {
            'response_time': current_metrics['performance']['avg_response_time_ms'],
            'error_rate': current_metrics['performance']['error_rate_percent'],
            'cultural_score': current_metrics['thai_sme_context']['avg_cultural_appropriateness']
        }
        
        for metric_name, current_value in current_values.items():
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]
                
                if baseline['std'] > 0:
                    z_score = abs(current_value - baseline['mean']) / baseline['std']
                    
                    if z_score > self.anomaly_threshold:
                        anomalies.append(
                            f"{metric_name}: {current_value} (z-score: {z_score:.2f})"
                        )
        
        return anomalies
    
    def _monitor_sla_compliance(self):
        """Monitor SLA compliance metrics"""
        current_metrics = metrics_collector.get_real_time_metrics()
        
        # Define SLA targets
        sla_targets = {
            'response_time_95th_percentile': 2000,  # 2 seconds
            'uptime_percentage': 99.9,
            'error_rate_max': 1.0,  # 1%
            'cultural_appropriateness_min': 0.8  # 80%
        }
        
        sla_status = {}
        
        # Check response time SLA
        avg_response = current_metrics['performance']['avg_response_time_ms']
        sla_status['response_time'] = avg_response <= sla_targets['response_time_95th_percentile']
        
        # Check error rate SLA
        error_rate = current_metrics['performance']['error_rate_percent']
        sla_status['error_rate'] = error_rate <= sla_targets['error_rate_max']
        
        # Check cultural appropriateness SLA
        cultural_score = current_metrics['thai_sme_context']['avg_cultural_appropriateness']
        sla_status['cultural_appropriateness'] = cultural_score >= sla_targets['cultural_appropriateness_min']
        
        # Log SLA violations
        for metric, is_compliant in sla_status.items():
            if not is_compliant:
                logger.warning(f"SLA VIOLATION: {metric} is not meeting targets")
        
        # Update overall SLA status
        overall_sla_compliance = all(sla_status.values())
        if not overall_sla_compliance:
            self.health_status['overall'] = 'sla_violation'
    
    def add_alert(self, alert: Alert):
        """Add a custom alert"""
        self.alerts[alert.alert_id] = alert
        logger.info(f"Added custom alert: {alert.name}")
    
    def remove_alert(self, alert_id: str):
        """Remove an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Removed alert: {alert_id}")
    
    def enable_alert(self, alert_id: str):
        """Enable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = True
            logger.info(f"Enabled alert: {alert_id}")
    
    def disable_alert(self, alert_id: str):
        """Disable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = False
            logger.info(f"Disabled alert: {alert_id}")
    
    def add_alert_handler(self, handler: Callable[[AlertEvent], None]):
        """Add alert notification handler"""
        self.alert_handlers.append(handler)
        logger.info("Added alert handler")
    
    def get_alert_history(self, hours: int = 24) -> List[AlertEvent]:
        """Get alert history for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
    
    def get_current_alerts(self) -> List[AlertEvent]:
        """Get currently active alerts"""
        current_time = time.time()
        active_alerts = []
        
        for alert in self.alert_history:
            # Consider alerts active if triggered within last hour
            if current_time - alert.timestamp <= 3600:
                active_alerts.append(alert)
        
        return active_alerts
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        current_metrics = metrics_collector.get_real_time_metrics()
        alert_history = self.get_alert_history(24)
        current_alerts = self.get_current_alerts()
        
        return {
            'timestamp': time.time(),
            'overall_health': self.health_status['overall'],
            'component_health': self.health_status,
            'current_metrics': current_metrics,
            'active_alerts_count': len(current_alerts),
            'alerts_last_24h': len(alert_history),
            'performance_trends': {
                name: {
                    'current': list(values)[-1] if values else 0,
                    'trend': self._get_trend_direction(list(values)) if len(values) >= 5 else 'stable'
                }
                for name, values in self.performance_trends.items()
            },
            'sla_compliance': self._calculate_sla_compliance(),
            'recommendations': self._generate_health_recommendations()
        }
    
    def _get_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction for a list of values"""
        if len(values) < 5:
            return 'stable'
        
        recent = sum(values[-3:]) / 3
        older = sum(values[-6:-3]) / 3
        
        if recent > older * 1.1:
            return 'increasing'
        elif recent < older * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_sla_compliance(self) -> Dict[str, float]:
        """Calculate SLA compliance percentages"""
        # This would be enhanced with actual SLA tracking
        return {
            'response_time_sla': 98.5,
            'error_rate_sla': 99.2,
            'uptime_sla': 99.8,
            'cultural_appropriateness_sla': 89.3
        }
    
    def _generate_health_recommendations(self) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        # Check performance trends
        if self.performance_trends['response_times']:
            avg_response = sum(self.performance_trends['response_times']) / len(self.performance_trends['response_times'])
            if avg_response > 2000:
                recommendations.append("Consider response time optimization - current average is high")
        
        if self.performance_trends['cost_per_hour']:
            avg_cost = sum(self.performance_trends['cost_per_hour']) / len(self.performance_trends['cost_per_hour'])
            if avg_cost > 3.0:
                recommendations.append("AI usage costs are high - review caching and model selection")
        
        # Check active alerts
        active_alerts = self.get_current_alerts()
        if len(active_alerts) > 5:
            recommendations.append("Multiple active alerts detected - investigate system issues")
        
        if not recommendations:
            recommendations.append("System performance is within normal parameters")
        
        return recommendations
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get AI-driven performance insights"""
        thai_sme_analytics = metrics_collector.get_thai_sme_analytics()
        cost_analytics = metrics_collector.get_cost_analytics()
        
        return {
            'cost_optimization': {
                'current_efficiency': cost_analytics['optimization_potential']['cache_hit_rate'],
                'potential_savings': cost_analytics['optimization_potential']['potential_monthly_savings'],
                'recommendations': cost_analytics['optimization_potential']['recommendations']
            },
            'thai_sme_effectiveness': {
                'cultural_performance': thai_sme_analytics['cultural_effectiveness'],
                'business_relevance': thai_sme_analytics['business_relevance'],
                'market_insights': thai_sme_analytics['market_insights']
            },
            'optimization_opportunities': self._identify_optimization_opportunities()
        }
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, str]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Cache optimization
        current_metrics = metrics_collector.get_real_time_metrics()
        cache_hit_rate = current_metrics['ai_usage']['cache_hit_rate_percent']
        
        if cache_hit_rate < 40:
            opportunities.append({
                'area': 'Caching',
                'description': 'Low cache hit rate detected',
                'recommendation': 'Implement semantic caching and increase TTL',
                'impact': 'High cost savings potential'
            })
        
        # Model optimization
        if current_metrics['ai_usage']['total_cost_usd'] > 10:
            opportunities.append({
                'area': 'Model Selection',
                'description': 'High AI usage costs',
                'recommendation': 'Review model selection strategy for simpler queries',
                'impact': 'Medium cost savings'
            })
        
        # Cultural effectiveness
        cultural_score = current_metrics['thai_sme_context']['avg_cultural_appropriateness']
        if cultural_score < 0.75:
            opportunities.append({
                'area': 'Thai SME Context',
                'description': 'Cultural appropriateness could be improved',
                'recommendation': 'Enhance cultural intelligence prompts',
                'impact': 'Better user experience'
            })
        
        return opportunities

# Global instance
monitoring_service = MonitoringService()

# Email alert handler example
def email_alert_handler(alert_event: AlertEvent):
    """Example email alert handler"""
    try:
        # This would be configured with actual SMTP settings
        logger.info(f"EMAIL ALERT: {alert_event.message}")
        # Actual email sending would be implemented here
    except Exception as e:
        logger.error(f"Email alert failed: {e}")

# Register default handlers
monitoring_service.add_alert_handler(email_alert_handler)