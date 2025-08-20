"""
Business Intelligence and Analytics System
Comprehensive analytics for OpenWebUI Platform
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of business metrics"""
    USAGE = "usage"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COST = "cost"
    USER_BEHAVIOR = "user_behavior"
    MODEL_PERFORMANCE = "model_performance"
    SYSTEM_HEALTH = "system_health"


class TimeRange(Enum):
    """Time range options for analytics"""
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"


@dataclass
class AnalyticsMetric:
    """Business intelligence metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    dimensions: Dict[str, Any]
    metadata: Dict[str, Any] = None


@dataclass
class UserSegment:
    """User segmentation data"""
    segment_id: str
    name: str
    user_count: int
    characteristics: Dict[str, Any]
    usage_patterns: Dict[str, Any]
    value_score: float


@dataclass
class ModelPerformanceMetrics:
    """Model performance analytics"""
    model_id: str
    model_name: str
    total_requests: int
    avg_response_time: float
    success_rate: float
    quality_score: float
    cost_per_request: float
    user_satisfaction: float
    top_use_cases: List[str]


@dataclass
class BusinessKPI:
    """Key Performance Indicator"""
    name: str
    current_value: float
    target_value: float
    trend: str  # "up", "down", "stable"
    change_percent: float
    status: str  # "healthy", "warning", "critical"


class BusinessIntelligenceEngine:
    """Core business intelligence and analytics engine"""
    
    def __init__(self, database_url: str, redis_url: str = None):
        self.database_url = database_url
        self.redis_url = redis_url
        self.engine = create_engine(database_url)
        self._cache = {}
        
    async def generate_executive_dashboard(self, time_range: TimeRange = TimeRange.WEEK) -> Dict[str, Any]:
        """Generate executive dashboard with key business metrics"""
        try:
            # Get time range boundaries
            end_date = datetime.now()
            start_date = self._get_start_date(end_date, time_range)
            
            # Parallel data collection
            tasks = [
                self._get_usage_metrics(start_date, end_date),
                self._get_performance_metrics(start_date, end_date),
                self._get_user_analytics(start_date, end_date),
                self._get_model_performance(start_date, end_date),
                self._get_cost_analytics(start_date, end_date),
                self._get_quality_metrics(start_date, end_date)
            ]
            
            results = await asyncio.gather(*tasks)
            usage_metrics, perf_metrics, user_analytics, model_perf, cost_metrics, quality_metrics = results
            
            # Calculate KPIs
            kpis = await self._calculate_business_kpis(start_date, end_date)
            
            # Generate insights and recommendations
            insights = await self._generate_business_insights({
                'usage': usage_metrics,
                'performance': perf_metrics,
                'users': user_analytics,
                'models': model_perf,
                'costs': cost_metrics,
                'quality': quality_metrics
            })
            
            dashboard = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'time_range': time_range.value
                },
                'key_metrics': {
                    'total_users': user_analytics.get('total_users', 0),
                    'active_users': user_analytics.get('active_users', 0),
                    'total_conversations': usage_metrics.get('total_conversations', 0),
                    'avg_session_length': usage_metrics.get('avg_session_length', 0),
                    'system_uptime': perf_metrics.get('uptime_percentage', 0),
                    'avg_response_time': perf_metrics.get('avg_response_time', 0)
                },
                'kpis': kpis,
                'usage_analytics': usage_metrics,
                'performance_analytics': perf_metrics,
                'user_analytics': user_analytics,
                'model_performance': model_perf,
                'cost_analytics': cost_metrics,
                'quality_analytics': quality_metrics,
                'insights': insights,
                'generated_at': datetime.now().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            return {'error': str(e)}
    
    async def _get_usage_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate usage metrics"""
        query = text("""
            SELECT 
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(DISTINCT c.user_id) as active_users,
                AVG(EXTRACT(EPOCH FROM (c.updated_at - c.created_at))/60) as avg_session_length_minutes,
                COUNT(m.id) as total_messages,
                AVG(LENGTH(m.content)) as avg_message_length,
                COUNT(DISTINCT DATE(c.created_at)) as active_days,
                COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) as ai_responses,
                COUNT(CASE WHEN m.role = 'user' THEN 1 END) as user_messages
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.created_at BETWEEN :start_date AND :end_date
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {'start_date': start_date, 'end_date': end_date}).fetchone()
            
        return {
            'total_conversations': result.total_conversations or 0,
            'active_users': result.active_users or 0,
            'avg_session_length': result.avg_session_length_minutes or 0,
            'total_messages': result.total_messages or 0,
            'avg_message_length': result.avg_message_length or 0,
            'active_days': result.active_days or 0,
            'ai_responses': result.ai_responses or 0,
            'user_messages': result.user_messages or 0,
            'messages_per_conversation': (result.total_messages or 0) / max(result.total_conversations or 1, 1),
            'conversations_per_user': (result.total_conversations or 0) / max(result.active_users or 1, 1)
        }
    
    async def _get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate system performance metrics"""
        # This would typically query monitoring systems like Prometheus
        # For now, we'll return simulated metrics
        
        return {
            'uptime_percentage': 99.95,
            'avg_response_time': 1.2,
            'p95_response_time': 2.8,
            'p99_response_time': 5.1,
            'error_rate': 0.05,
            'throughput_rpm': 1250,
            'cpu_utilization': 45.2,
            'memory_utilization': 62.8,
            'disk_utilization': 23.4,
            'network_throughput_mbps': 89.3
        }
    
    async def _get_user_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze user behavior and segments"""
        # User segmentation query
        user_query = text("""
            SELECT 
                u.id,
                u.email,
                u.created_at as signup_date,
                COUNT(DISTINCT c.id) as conversation_count,
                COUNT(m.id) as message_count,
                MAX(c.updated_at) as last_activity,
                AVG(EXTRACT(EPOCH FROM (c.updated_at - c.created_at))/60) as avg_session_length,
                COUNT(DISTINCT DATE(c.created_at)) as active_days
            FROM users u
            LEFT JOIN conversations c ON u.id = c.user_id
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE u.created_at <= :end_date
            GROUP BY u.id, u.email, u.created_at
        """)
        
        with self.engine.connect() as conn:
            user_data = conn.execute(user_query, {'end_date': end_date}).fetchall()
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([dict(row._mapping) for row in user_data])
        
        if df.empty:
            return {'total_users': 0, 'active_users': 0, 'segments': []}
        
        # Calculate user segments using clustering
        segments = await self._segment_users(df)
        
        # Calculate retention metrics
        retention = await self._calculate_user_retention(df, start_date, end_date)
        
        total_users = len(df)
        active_users = len(df[df['last_activity'] >= start_date])
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_period': len(df[df['signup_date'] >= start_date]),
            'user_retention': retention,
            'user_segments': segments,
            'avg_conversations_per_user': df['conversation_count'].mean(),
            'avg_messages_per_user': df['message_count'].mean(),
            'avg_session_length': df['avg_session_length'].mean(),
            'most_active_users': df.nlargest(10, 'message_count')[['email', 'message_count']].to_dict('records')
        }
    
    async def _segment_users(self, user_df: pd.DataFrame) -> List[UserSegment]:
        """Segment users based on usage patterns"""
        if len(user_df) < 3:
            return []
        
        # Features for clustering
        features = ['conversation_count', 'message_count', 'active_days', 'avg_session_length']
        feature_data = user_df[features].fillna(0)
        
        # Normalize features
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(feature_data)
        
        # Determine optimal number of clusters (max 5)
        n_clusters = min(5, len(user_df) // 2)
        if n_clusters < 2:
            n_clusters = 2
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        user_df['segment'] = kmeans.fit_predict(normalized_data)
        
        # Analyze segments
        segments = []
        for segment_id in range(n_clusters):
            segment_users = user_df[user_df['segment'] == segment_id]
            
            # Calculate segment characteristics
            characteristics = {
                'avg_conversations': segment_users['conversation_count'].mean(),
                'avg_messages': segment_users['message_count'].mean(),
                'avg_active_days': segment_users['active_days'].mean(),
                'avg_session_length': segment_users['avg_session_length'].mean()
            }
            
            # Determine segment name based on characteristics
            segment_name = self._name_user_segment(characteristics)
            
            # Calculate value score (higher usage = higher value)
            value_score = (
                characteristics['avg_conversations'] * 0.3 +
                characteristics['avg_messages'] * 0.4 +
                characteristics['avg_active_days'] * 0.3
            )
            
            segment = UserSegment(
                segment_id=str(segment_id),
                name=segment_name,
                user_count=len(segment_users),
                characteristics=characteristics,
                usage_patterns={
                    'peak_usage_hour': self._calculate_peak_hour(segment_users),
                    'preferred_session_length': characteristics['avg_session_length']
                },
                value_score=value_score
            )
            
            segments.append(asdict(segment))
        
        return segments
    
    def _name_user_segment(self, characteristics: Dict[str, float]) -> str:
        """Generate descriptive names for user segments"""
        avg_conversations = characteristics['avg_conversations']
        avg_messages = characteristics['avg_messages']
        
        if avg_conversations >= 10 and avg_messages >= 50:
            return "Power Users"
        elif avg_conversations >= 5 and avg_messages >= 20:
            return "Regular Users"
        elif avg_conversations >= 2 and avg_messages >= 5:
            return "Casual Users"
        else:
            return "Trial Users"
    
    def _calculate_peak_hour(self, segment_users: pd.DataFrame) -> int:
        """Calculate peak usage hour for a segment (simulated)"""
        # This would typically analyze actual usage timestamps
        # For now, return a simulated peak hour
        return np.random.randint(9, 17)  # Business hours
    
    async def _calculate_user_retention(self, user_df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate user retention metrics"""
        # This is a simplified calculation
        # In production, you'd analyze actual user activity patterns
        
        total_users = len(user_df)
        if total_users == 0:
            return {'day_1': 0, 'day_7': 0, 'day_30': 0}
        
        # Users active in the last day, week, month
        last_day = end_date - timedelta(days=1)
        last_week = end_date - timedelta(days=7)
        last_month = end_date - timedelta(days=30)
        
        day_1_retention = len(user_df[user_df['last_activity'] >= last_day]) / total_users * 100
        day_7_retention = len(user_df[user_df['last_activity'] >= last_week]) / total_users * 100
        day_30_retention = len(user_df[user_df['last_activity'] >= last_month]) / total_users * 100
        
        return {
            'day_1': day_1_retention,
            'day_7': day_7_retention,
            'day_30': day_30_retention
        }
    
    async def _get_model_performance(self, start_date: datetime, end_date: datetime) -> List[ModelPerformanceMetrics]:
        """Analyze AI model performance"""
        # This would typically query model usage logs
        # For now, return simulated data
        
        models = [
            ModelPerformanceMetrics(
                model_id="llama2-7b",
                model_name="Llama 2 7B",
                total_requests=15420,
                avg_response_time=2.3,
                success_rate=98.5,
                quality_score=4.2,
                cost_per_request=0.003,
                user_satisfaction=4.1,
                top_use_cases=["General Chat", "Code Assistance", "Writing Help"]
            ),
            ModelPerformanceMetrics(
                model_id="codellama-13b",
                model_name="Code Llama 13B",
                total_requests=8930,
                avg_response_time=3.8,
                success_rate=97.2,
                quality_score=4.5,
                cost_per_request=0.007,
                user_satisfaction=4.3,
                top_use_cases=["Code Generation", "Debugging", "Code Review"]
            )
        ]
        
        return [asdict(model) for model in models]
    
    async def _get_cost_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate cost analytics and optimization recommendations"""
        # This would typically integrate with cloud billing APIs
        # For now, return simulated cost data
        
        return {
            'total_cost_period': 1247.83,
            'cost_breakdown': {
                'compute': 892.34,
                'storage': 234.67,
                'network': 89.23,
                'monitoring': 31.59
            },
            'cost_per_user': 31.20,
            'cost_per_conversation': 0.85,
            'cost_per_message': 0.12,
            'cost_trend': {
                'change_percent': -12.5,
                'trend': 'down',
                'driver': 'Improved model efficiency'
            },
            'optimization_savings': 187.42,
            'recommendations': [
                {
                    'category': 'Model Optimization',
                    'description': 'Switch to more efficient model for simple queries',
                    'potential_savings': 89.34
                },
                {
                    'category': 'Resource Scaling',
                    'description': 'Implement auto-scaling to reduce idle resources',
                    'potential_savings': 54.23
                }
            ]
        }
    
    async def _get_quality_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate response quality and user satisfaction metrics"""
        # This would typically analyze user feedback, ratings, and behavior
        # For now, return simulated quality metrics
        
        return {
            'avg_response_quality': 4.2,
            'user_satisfaction_score': 4.1,
            'response_accuracy': 87.3,
            'response_relevance': 89.6,
            'response_completeness': 82.4,
            'user_feedback_volume': 423,
            'positive_feedback_ratio': 0.78,
            'quality_trends': {
                'response_quality_trend': 'up',
                'satisfaction_trend': 'stable',
                'accuracy_trend': 'up'
            },
            'improvement_areas': [
                'Response completeness for technical queries',
                'Handling of ambiguous questions',
                'Multi-step reasoning tasks'
            ]
        }
    
    async def _calculate_business_kpis(self, start_date: datetime, end_date: datetime) -> List[BusinessKPI]:
        """Calculate key business performance indicators"""
        # This would calculate actual KPIs based on business goals
        # For now, return simulated KPIs
        
        kpis = [
            BusinessKPI(
                name="Monthly Active Users",
                current_value=1247,
                target_value=1500,
                trend="up",
                change_percent=12.3,
                status="healthy"
            ),
            BusinessKPI(
                name="Average Session Length (minutes)",
                current_value=18.5,
                target_value=20.0,
                trend="up",
                change_percent=8.2,
                status="healthy"
            ),
            BusinessKPI(
                name="System Uptime (%)",
                current_value=99.95,
                target_value=99.9,
                trend="stable",
                change_percent=0.1,
                status="healthy"
            ),
            BusinessKPI(
                name="Cost per User ($)",
                current_value=31.20,
                target_value=25.0,
                trend="down",
                change_percent=-12.5,
                status="warning"
            ),
            BusinessKPI(
                name="User Satisfaction Score",
                current_value=4.1,
                target_value=4.5,
                trend="up",
                change_percent=5.1,
                status="healthy"
            )
        ]
        
        return [asdict(kpi) for kpi in kpis]
    
    async def _generate_business_insights(self, analytics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered business insights and recommendations"""
        insights = []
        
        # Usage insights
        usage = analytics_data['usage']
        if usage.get('messages_per_conversation', 0) > 15:
            insights.append({
                'category': 'User Engagement',
                'insight': 'Users are having longer conversations, indicating high engagement',
                'recommendation': 'Consider introducing advanced features for power users',
                'impact': 'High',
                'confidence': 0.85
            })
        
        # Performance insights
        perf = analytics_data['performance']
        if perf.get('avg_response_time', 0) > 2.0:
            insights.append({
                'category': 'System Performance',
                'insight': 'Response times are above optimal threshold',
                'recommendation': 'Investigate model optimization or infrastructure scaling',
                'impact': 'Medium',
                'confidence': 0.92
            })
        
        # Cost insights
        costs = analytics_data['costs']
        if costs.get('cost_per_user', 0) > 30:
            insights.append({
                'category': 'Cost Optimization',
                'insight': 'Cost per user is above industry benchmarks',
                'recommendation': 'Implement tiered pricing or optimize resource allocation',
                'impact': 'High',
                'confidence': 0.78
            })
        
        # Quality insights
        quality = analytics_data['quality']
        if quality.get('avg_response_quality', 0) < 4.0:
            insights.append({
                'category': 'Response Quality',
                'insight': 'Response quality scores indicate room for improvement',
                'recommendation': 'Fine-tune models or improve prompt engineering',
                'impact': 'Medium',
                'confidence': 0.89
            })
        
        return insights
    
    def _get_start_date(self, end_date: datetime, time_range: TimeRange) -> datetime:
        """Calculate start date based on time range"""
        range_map = {
            TimeRange.HOUR: timedelta(hours=1),
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(days=7),
            TimeRange.MONTH: timedelta(days=30),
            TimeRange.QUARTER: timedelta(days=90),
            TimeRange.YEAR: timedelta(days=365)
        }
        
        return end_date - range_map[time_range]
    
    async def generate_predictive_analytics(self, metric: str, forecast_days: int = 30) -> Dict[str, Any]:
        """Generate predictive analytics for key metrics"""
        # This would use ML models for prediction
        # For now, return simulated predictions
        
        base_value = 1000  # Simulated current value
        predictions = []
        
        for day in range(1, forecast_days + 1):
            # Simple trend simulation
            trend_factor = 1.02 ** day  # 2% daily growth
            noise = np.random.normal(0, 0.05)  # 5% noise
            predicted_value = base_value * trend_factor * (1 + noise)
            
            predictions.append({
                'date': (datetime.now() + timedelta(days=day)).isoformat(),
                'predicted_value': round(predicted_value, 2),
                'confidence_interval': {
                    'lower': round(predicted_value * 0.9, 2),
                    'upper': round(predicted_value * 1.1, 2)
                }
            })
        
        return {
            'metric': metric,
            'forecast_period_days': forecast_days,
            'predictions': predictions,
            'model_accuracy': 0.85,
            'trend_analysis': {
                'direction': 'upward',
                'strength': 'strong',
                'volatility': 'low'
            },
            'generated_at': datetime.now().isoformat()
        }