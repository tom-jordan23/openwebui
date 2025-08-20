"""
Assistant Performance Analytics API
Provides comprehensive analytics and monitoring for AI assistants
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from functools import wraps
from flask import Blueprint, request, jsonify, g

from ..database.assistant_repositories import (
    AssistantRepository,
    AssistantAnalyticsRepository,
    ConversationContextRepository
)
from ..database.assistant_models import AssistantProfile, AssistantType
from ..database.connection import get_db_connection

logger = logging.getLogger(__name__)

# Create Blueprint
analytics_bp = Blueprint('assistant_analytics', __name__, url_prefix='/api/v1/assistants')


class AnalyticsService:
    """Core service for assistant analytics and performance monitoring"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.assistant_repo = AssistantRepository()
        self.analytics_repo = AssistantAnalyticsRepository()
        self.context_repo = ConversationContextRepository()
    
    def get_assistant_metrics(self, assistant_id: str, user_id: str, days: int = 30, 
                             metrics: List[str] = None) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Get comprehensive metrics for an assistant"""
        try:
            # Check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Get basic performance summary
            performance_summary = self.assistant_repo.get_performance_summary(assistant_id)
            
            # Get detailed analytics
            all_metrics = self.analytics_repo.get_metrics(assistant_id, days=days)
            aggregated_metrics = self.analytics_repo.get_aggregated_metrics(assistant_id, days)
            
            # Filter metrics if specified
            if metrics:
                all_metrics = [m for m in all_metrics if m['metric_name'] in metrics]
                aggregated_metrics = {k: v for k, v in aggregated_metrics.items() if k in metrics}
            
            # Calculate trend data
            trend_data = self._calculate_trends(all_metrics, days)
            
            # Get conversation insights
            conversation_insights = self._get_conversation_insights(assistant_id, days)
            
            # Compile comprehensive metrics
            metrics_data = {
                'assistant_id': assistant_id,
                'assistant_name': assistant.name,
                'report_period_days': days,
                'generated_at': int(time.time() * 1000),
                'basic_stats': {
                    'total_conversations': assistant.total_conversations,
                    'total_messages': assistant.total_messages,
                    'avg_conversation_length': assistant.avg_conversation_length,
                    'avg_response_time': assistant.avg_response_time,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'assistant_type': assistant.assistant_type.value,
                    'status': assistant.status.value,
                    'version': assistant.version
                },
                'performance_summary': performance_summary,
                'detailed_metrics': aggregated_metrics,
                'trends': trend_data,
                'conversation_insights': conversation_insights,
                'raw_metrics_count': len(all_metrics)
            }
            
            return True, metrics_data
            
        except Exception as e:
            logger.error(f"Error getting metrics for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_usage_analytics(self, assistant_id: str, user_id: str, 
                           time_period: str = 'daily', days: int = 30) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Get detailed usage analytics over time"""
        try:
            # Check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Validate time period
            if time_period not in ['hourly', 'daily', 'weekly', 'monthly']:
                return False, "Invalid time period. Valid options: hourly, daily, weekly, monthly"
            
            # Get time-series data
            usage_metrics = self.analytics_repo.get_metrics(
                assistant_id, 
                time_period=time_period, 
                days=days
            )
            
            # Process usage data
            usage_data = self._process_usage_data(usage_metrics, time_period, days)
            
            # Get active sessions data
            active_sessions = self.context_repo.get_active_sessions(assistant_id, 24)
            
            result = {
                'assistant_id': assistant_id,
                'time_period': time_period,
                'report_period_days': days,
                'usage_timeline': usage_data['timeline'],
                'usage_summary': usage_data['summary'],
                'peak_usage': usage_data['peak_usage'],
                'active_sessions': len(active_sessions),
                'session_details': [
                    {
                        'session_id': session.session_id,
                        'started_at': session.started_at,
                        'last_interaction': session.last_interaction,
                        'interaction_count': session.interaction_count,
                        'avg_response_time': session.avg_response_time,
                        'total_tokens_used': session.total_tokens_used
                    }
                    for session in active_sessions[:10]  # Limit to first 10 sessions
                ]
            }
            
            return True, result
            
        except Exception as e:
            logger.error(f"Error getting usage analytics for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_performance_comparison(self, assistant_ids: List[str], user_id: str, 
                                  days: int = 30) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Compare performance metrics across multiple assistants"""
        try:
            if len(assistant_ids) < 2 or len(assistant_ids) > 10:
                return False, "Comparison requires 2-10 assistants"
            
            comparison_data = {
                'comparison_period_days': days,
                'assistants': [],
                'metrics_comparison': {},
                'rankings': {}
            }
            
            all_assistants = []
            for assistant_id in assistant_ids:
                assistant = self.assistant_repo.get_by_id(assistant_id)
                if not assistant:
                    continue
                
                # Check basic permission (user's own assistants or public ones)
                if assistant.user_id != user_id:
                    continue
                
                # Get metrics for this assistant
                aggregated_metrics = self.analytics_repo.get_aggregated_metrics(assistant_id, days)
                
                assistant_data = {
                    'assistant_id': assistant_id,
                    'name': assistant.name,
                    'type': assistant.assistant_type.value,
                    'total_conversations': assistant.total_conversations,
                    'avg_response_time': assistant.avg_response_time,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'metrics': aggregated_metrics
                }
                
                all_assistants.append(assistant_data)
                comparison_data['assistants'].append(assistant_data)
            
            if len(all_assistants) < 2:
                return False, "Insufficient assistants available for comparison"
            
            # Calculate comparison metrics
            comparison_data['metrics_comparison'] = self._calculate_comparison_metrics(all_assistants)
            comparison_data['rankings'] = self._calculate_rankings(all_assistants)
            
            return True, comparison_data
            
        except Exception as e:
            logger.error(f"Error comparing assistant performance: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_health_status(self, assistant_id: str, user_id: str) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Get current health status and alerts for an assistant"""
        try:
            # Check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Get recent metrics (last 24 hours)
            recent_metrics = self.analytics_repo.get_metrics(assistant_id, days=1)
            
            # Get recent error logs
            recent_errors = assistant.error_logs[-10:] if assistant.error_logs else []
            
            # Calculate health score
            health_score = self._calculate_health_score(assistant, recent_metrics, recent_errors)
            
            # Get deployment status
            deployment_status = self.assistant_repo.get_deployment_status(assistant_id)
            
            # Generate alerts
            alerts = self._generate_alerts(assistant, recent_metrics, recent_errors)
            
            health_data = {
                'assistant_id': assistant_id,
                'health_score': health_score['score'],
                'health_grade': health_score['grade'],
                'status': assistant.status.value,
                'is_active': assistant.is_active,
                'last_updated': assistant.updated_at,
                'deployment_status': deployment_status,
                'performance_indicators': health_score['indicators'],
                'recent_errors': len(recent_errors),
                'error_details': recent_errors,
                'alerts': alerts,
                'recommendations': health_score['recommendations']
            }
            
            return True, health_data
            
        except Exception as e:
            logger.error(f"Error getting health status for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_user_analytics_summary(self, user_id: str, days: int = 30) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Get analytics summary for all user's assistants"""
        try:
            # Get all user assistants
            assistants = self.assistant_repo.get_by_user_id(user_id, include_archived=False)
            
            if not assistants:
                return True, {
                    'total_assistants': 0,
                    'active_assistants': 0,
                    'summary_metrics': {},
                    'top_performers': [],
                    'needs_attention': []
                }
            
            # Calculate aggregate metrics
            total_conversations = sum(a.total_conversations for a in assistants)
            total_messages = sum(a.total_messages for a in assistants)
            avg_satisfaction = sum(a.user_satisfaction_rating for a in assistants) / len(assistants)
            
            # Find top performers and problematic assistants
            top_performers = sorted(
                [a for a in assistants if a.total_conversations > 0], 
                key=lambda x: (x.user_satisfaction_rating, x.total_conversations), 
                reverse=True
            )[:5]
            
            needs_attention = [
                a for a in assistants 
                if a.user_satisfaction_rating < 3.0 or len(a.error_logs) > 5 or not a.is_active
            ]
            
            # Get recent activity
            recent_activity = []
            for assistant in assistants[:10]:  # Limit to top 10 assistants
                recent_sessions = self.context_repo.get_active_sessions(assistant.id, 24)
                if recent_sessions:
                    recent_activity.append({
                        'assistant_id': assistant.id,
                        'assistant_name': assistant.name,
                        'active_sessions': len(recent_sessions),
                        'last_interaction': max(s.last_interaction for s in recent_sessions) if recent_sessions else 0
                    })
            
            summary = {
                'user_id': user_id,
                'report_period_days': days,
                'generated_at': int(time.time() * 1000),
                'total_assistants': len(assistants),
                'active_assistants': len([a for a in assistants if a.is_active]),
                'summary_metrics': {
                    'total_conversations': total_conversations,
                    'total_messages': total_messages,
                    'avg_satisfaction_rating': round(avg_satisfaction, 2),
                    'avg_response_time': sum(a.avg_response_time for a in assistants) / len(assistants)
                },
                'assistant_types': {
                    t.value: len([a for a in assistants if a.assistant_type == t])
                    for t in AssistantType
                },
                'top_performers': [
                    {
                        'assistant_id': a.id,
                        'name': a.name,
                        'satisfaction_rating': a.user_satisfaction_rating,
                        'total_conversations': a.total_conversations,
                        'type': a.assistant_type.value
                    }
                    for a in top_performers
                ],
                'needs_attention': [
                    {
                        'assistant_id': a.id,
                        'name': a.name,
                        'issues': self._identify_issues(a),
                        'satisfaction_rating': a.user_satisfaction_rating,
                        'error_count': len(a.error_logs)
                    }
                    for a in needs_attention
                ],
                'recent_activity': recent_activity
            }
            
            return True, summary
            
        except Exception as e:
            logger.error(f"Error getting user analytics summary for {user_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def _calculate_trends(self, metrics: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """Calculate trend analysis for metrics"""
        if not metrics:
            return {}
        
        # Group metrics by name and calculate trends
        metric_groups = {}
        for metric in metrics:
            name = metric['metric_name']
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(metric)
        
        trends = {}
        for metric_name, metric_list in metric_groups.items():
            # Sort by time
            sorted_metrics = sorted(metric_list, key=lambda x: x['recorded_at'])
            
            if len(sorted_metrics) >= 2:
                recent_avg = sum(m['metric_value'] for m in sorted_metrics[-7:]) / min(7, len(sorted_metrics))
                older_avg = sum(m['metric_value'] for m in sorted_metrics[:7]) / min(7, len(sorted_metrics))
                
                if older_avg > 0:
                    trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
                else:
                    trend_percentage = 0
                
                trends[metric_name] = {
                    'direction': 'up' if trend_percentage > 5 else 'down' if trend_percentage < -5 else 'stable',
                    'percentage': round(trend_percentage, 2),
                    'recent_average': round(recent_avg, 2),
                    'data_points': len(sorted_metrics)
                }
        
        return trends
    
    def _get_conversation_insights(self, assistant_id: str, days: int) -> Dict[str, Any]:
        """Get insights about conversation patterns"""
        try:
            # Get active sessions for analysis
            active_sessions = self.context_repo.get_active_sessions(assistant_id, days * 24)
            
            if not active_sessions:
                return {}
            
            # Analyze conversation patterns
            conversation_lengths = [len(s.conversation_history) for s in active_sessions]
            response_times = [s.avg_response_time for s in active_sessions if s.avg_response_time > 0]
            
            return {
                'total_sessions': len(active_sessions),
                'avg_conversation_length': round(sum(conversation_lengths) / len(conversation_lengths), 2) if conversation_lengths else 0,
                'median_conversation_length': sorted(conversation_lengths)[len(conversation_lengths)//2] if conversation_lengths else 0,
                'avg_session_response_time': round(sum(response_times) / len(response_times), 3) if response_times else 0,
                'total_tokens_consumed': sum(s.total_tokens_used for s in active_sessions),
                'error_rate': sum(s.errors_encountered for s in active_sessions) / len(active_sessions) if active_sessions else 0
            }
        except Exception:
            return {}
    
    def _process_usage_data(self, metrics: List[Dict[str, Any]], time_period: str, days: int) -> Dict[str, Any]:
        """Process raw metrics into usage timeline and summary"""
        timeline = []
        summary = {
            'total_interactions': 0,
            'peak_hour': None,
            'peak_day': None,
            'avg_daily_usage': 0
        }
        
        # Group metrics by time period
        time_groups = {}
        for metric in metrics:
            timestamp = metric['recorded_at']
            # Create time period key based on granularity
            if time_period == 'hourly':
                time_key = timestamp - (timestamp % (60 * 60 * 1000))  # Round to hour
            elif time_period == 'daily':
                time_key = timestamp - (timestamp % (24 * 60 * 60 * 1000))  # Round to day
            else:
                time_key = timestamp
            
            if time_key not in time_groups:
                time_groups[time_key] = []
            time_groups[time_key].append(metric)
        
        # Create timeline
        for time_key in sorted(time_groups.keys()):
            metrics_in_period = time_groups[time_key]
            interaction_count = len([m for m in metrics_in_period if m['metric_name'] == 'conversation_length'])
            
            timeline.append({
                'timestamp': time_key,
                'interactions': interaction_count,
                'avg_response_time': sum(m['metric_value'] for m in metrics_in_period if m['metric_name'] == 'response_time') / max(1, len([m for m in metrics_in_period if m['metric_name'] == 'response_time'])),
                'tokens_used': sum(m['metric_value'] for m in metrics_in_period if m['metric_name'] == 'tokens_used')
            })
            
            summary['total_interactions'] += interaction_count
        
        # Find peak usage
        if timeline:
            peak_usage = max(timeline, key=lambda x: x['interactions'])
            summary['peak_usage'] = {
                'timestamp': peak_usage['timestamp'],
                'interactions': peak_usage['interactions']
            }
        
        return {
            'timeline': timeline,
            'summary': summary,
            'peak_usage': summary.get('peak_usage', {})
        }
    
    def _calculate_comparison_metrics(self, assistants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comparison metrics across assistants"""
        if not assistants:
            return {}
        
        # Extract common metrics
        response_times = [a['avg_response_time'] for a in assistants if a['avg_response_time'] > 0]
        satisfaction_ratings = [a['user_satisfaction_rating'] for a in assistants]
        conversation_counts = [a['total_conversations'] for a in assistants]
        
        return {
            'response_time': {
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'avg': sum(response_times) / len(response_times) if response_times else 0
            },
            'satisfaction': {
                'min': min(satisfaction_ratings),
                'max': max(satisfaction_ratings),
                'avg': sum(satisfaction_ratings) / len(satisfaction_ratings)
            },
            'usage': {
                'min': min(conversation_counts),
                'max': max(conversation_counts),
                'total': sum(conversation_counts)
            }
        }
    
    def _calculate_rankings(self, assistants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate rankings for different metrics"""
        rankings = {}
        
        # Rank by satisfaction
        satisfaction_ranked = sorted(assistants, key=lambda x: x['user_satisfaction_rating'], reverse=True)
        rankings['satisfaction'] = [
            {'assistant_id': a['assistant_id'], 'name': a['name'], 'value': a['user_satisfaction_rating']}
            for a in satisfaction_ranked
        ]
        
        # Rank by usage
        usage_ranked = sorted(assistants, key=lambda x: x['total_conversations'], reverse=True)
        rankings['usage'] = [
            {'assistant_id': a['assistant_id'], 'name': a['name'], 'value': a['total_conversations']}
            for a in usage_ranked
        ]
        
        # Rank by response time (lower is better)
        response_time_ranked = sorted(
            [a for a in assistants if a['avg_response_time'] > 0], 
            key=lambda x: x['avg_response_time']
        )
        rankings['response_time'] = [
            {'assistant_id': a['assistant_id'], 'name': a['name'], 'value': a['avg_response_time']}
            for a in response_time_ranked
        ]
        
        return rankings
    
    def _calculate_health_score(self, assistant: AssistantProfile, 
                               recent_metrics: List[Dict[str, Any]], 
                               recent_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall health score for an assistant"""
        score = 100  # Start with perfect score
        indicators = {}
        recommendations = []
        
        # Factor 1: User satisfaction (0-40 points)
        satisfaction_score = assistant.user_satisfaction_rating * 8  # Scale to 40 points
        score = min(score, 60 + satisfaction_score)
        indicators['satisfaction'] = {
            'score': satisfaction_score,
            'status': 'good' if satisfaction_score >= 24 else 'warning' if satisfaction_score >= 16 else 'critical'
        }
        
        if satisfaction_score < 24:
            recommendations.append("Improve user satisfaction by reviewing prompts and responses")
        
        # Factor 2: Error rate (0-30 points deduction)
        error_count = len(recent_errors)
        error_deduction = min(error_count * 3, 30)
        score -= error_deduction
        indicators['errors'] = {
            'count': error_count,
            'status': 'good' if error_count <= 2 else 'warning' if error_count <= 5 else 'critical'
        }
        
        if error_count > 2:
            recommendations.append(f"Address {error_count} recent errors to improve stability")
        
        # Factor 3: Response time (0-20 points deduction)
        if assistant.avg_response_time > 5.0:
            response_time_deduction = min((assistant.avg_response_time - 5.0) * 2, 20)
            score -= response_time_deduction
        
        indicators['response_time'] = {
            'avg': assistant.avg_response_time,
            'status': 'good' if assistant.avg_response_time <= 3.0 else 'warning' if assistant.avg_response_time <= 5.0 else 'critical'
        }
        
        if assistant.avg_response_time > 5.0:
            recommendations.append("Optimize response time by reviewing model configuration")
        
        # Factor 4: Activity level
        if assistant.total_conversations == 0:
            score -= 10
            recommendations.append("Assistant has no conversations - consider promotion or testing")
        
        indicators['activity'] = {
            'conversations': assistant.total_conversations,
            'status': 'good' if assistant.total_conversations >= 10 else 'warning' if assistant.total_conversations >= 1 else 'critical'
        }
        
        # Determine grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': max(0, round(score)),
            'grade': grade,
            'indicators': indicators,
            'recommendations': recommendations
        }
    
    def _generate_alerts(self, assistant: AssistantProfile, 
                        recent_metrics: List[Dict[str, Any]], 
                        recent_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alerts based on assistant performance"""
        alerts = []
        
        # High error rate alert
        if len(recent_errors) > 5:
            alerts.append({
                'type': 'error_rate',
                'severity': 'high',
                'message': f"High error rate detected: {len(recent_errors)} errors in the last 24 hours",
                'action': "Review error logs and fix underlying issues"
            })
        
        # Low satisfaction alert
        if assistant.user_satisfaction_rating < 2.5 and assistant.total_conversations > 5:
            alerts.append({
                'type': 'satisfaction',
                'severity': 'medium',
                'message': f"Low user satisfaction rating: {assistant.user_satisfaction_rating}/5.0",
                'action': "Review and improve prompts, responses, or configuration"
            })
        
        # Slow response time alert
        if assistant.avg_response_time > 10.0:
            alerts.append({
                'type': 'performance',
                'severity': 'medium',
                'message': f"Slow average response time: {assistant.avg_response_time}s",
                'action': "Optimize model configuration or increase resources"
            })
        
        # Inactive assistant alert
        if not assistant.is_active:
            alerts.append({
                'type': 'status',
                'severity': 'low',
                'message': "Assistant is inactive",
                'action': "Activate assistant if it should be available for use"
            })
        
        return alerts
    
    def _identify_issues(self, assistant: AssistantProfile) -> List[str]:
        """Identify specific issues with an assistant"""
        issues = []
        
        if not assistant.is_active:
            issues.append("inactive")
        
        if assistant.user_satisfaction_rating < 3.0:
            issues.append("low_satisfaction")
        
        if len(assistant.error_logs) > 5:
            issues.append("high_errors")
        
        if assistant.avg_response_time > 8.0:
            issues.append("slow_response")
        
        if assistant.total_conversations == 0:
            issues.append("no_usage")
        
        return issues


# Initialize service
analytics_service = AnalyticsService()


def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# API Endpoints
@analytics_bp.route('/<assistant_id>/metrics', methods=['GET'])
@require_user_id
def get_assistant_metrics(assistant_id: str):
    """Get comprehensive metrics for an assistant"""
    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(days, 365))  # Between 1 day and 1 year
        
        metrics_filter = request.args.get('metrics')
        metrics_list = metrics_filter.split(',') if metrics_filter else None
        
        success, result = analytics_service.get_assistant_metrics(
            assistant_id, g.user_id, days, metrics_list
        )
        
        if success:
            return jsonify({'metrics': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        logger.error(f"Error in get_assistant_metrics endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/<assistant_id>/usage', methods=['GET'])
@require_user_id
def get_usage_analytics(assistant_id: str):
    """Get detailed usage analytics over time"""
    try:
        time_period = request.args.get('period', 'daily')
        days = int(request.args.get('days', 30))
        days = max(1, min(days, 365))
        
        success, result = analytics_service.get_usage_analytics(
            assistant_id, g.user_id, time_period, days
        )
        
        if success:
            return jsonify({'usage': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400
    except Exception as e:
        logger.error(f"Error in get_usage_analytics endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/compare', methods=['POST'])
@require_user_id
def compare_assistants():
    """Compare performance metrics across multiple assistants"""
    try:
        data = request.get_json()
        if not data or 'assistant_ids' not in data:
            return jsonify({'error': 'assistant_ids array is required'}), 400
        
        assistant_ids = data['assistant_ids']
        days = data.get('days', 30)
        
        if not isinstance(assistant_ids, list):
            return jsonify({'error': 'assistant_ids must be an array'}), 400
        
        success, result = analytics_service.get_performance_comparison(
            assistant_ids, g.user_id, days
        )
        
        if success:
            return jsonify({'comparison': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in compare_assistants endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/<assistant_id>/health', methods=['GET'])
@require_user_id
def get_health_status(assistant_id: str):
    """Get current health status and alerts for an assistant"""
    try:
        success, result = analytics_service.get_health_status(assistant_id, g.user_id)
        
        if success:
            return jsonify({'health': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_health_status endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/summary', methods=['GET'])
@require_user_id
def get_user_analytics_summary():
    """Get analytics summary for all user's assistants"""
    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(days, 365))
        
        success, result = analytics_service.get_user_analytics_summary(g.user_id, days)
        
        if success:
            return jsonify({'summary': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        logger.error(f"Error in get_user_analytics_summary endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500