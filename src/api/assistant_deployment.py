"""
Assistant Deployment and Lifecycle Management API
Handles deployment of assistants across environments and manages their lifecycle
"""

import logging
import time
import json
from typing import List, Dict, Optional, Any, Union
from functools import wraps
from flask import Blueprint, request, jsonify, g

from ..database.assistant_repositories import (
    AssistantRepository,
    AssistantDeploymentRepository,
    AssistantAnalyticsRepository
)
from ..database.assistant_models import (
    AssistantProfile, AssistantDeployment,
    AssistantStatus, DeploymentEnvironment
)

logger = logging.getLogger(__name__)

# Create Blueprint
deployment_bp = Blueprint('assistant_deployment', __name__, url_prefix='/api/v1/assistants')


class DeploymentService:
    """Core service for assistant deployment and lifecycle management"""
    
    def __init__(self):
        self.assistant_repo = AssistantRepository()
        self.deployment_repo = AssistantDeploymentRepository()
        self.analytics_repo = AssistantAnalyticsRepository()
    
    def deploy_assistant(self, assistant_id: str, environment: str, user_id: str, 
                        deployment_config: Dict[str, Any] = None) -> tuple[bool, Union[AssistantDeployment, str]]:
        """Deploy an assistant to a specific environment"""
        try:
            # Validate environment
            try:
                env_enum = DeploymentEnvironment(environment)
            except ValueError:
                return False, f"Invalid deployment environment: {environment}"
            
            # Get and validate assistant
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            # Check if user has permission to deploy this assistant
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Check if assistant can be deployed to this environment
            can_deploy, reason = assistant.can_deploy_to(env_enum)
            if not can_deploy:
                return False, reason
            
            # Check for existing active deployment in this environment
            existing_deployment = self.deployment_repo.get_active_deployment(assistant_id, env_enum)
            if existing_deployment:
                return False, f"Assistant already has an active deployment in {environment}"
            
            # Create deployment record
            deployment = AssistantDeployment(
                assistant_id=assistant_id,
                environment=env_enum,
                version=assistant.version,
                deployed_by=user_id,
                configuration_snapshot={
                    'system_prompt': assistant.system_prompt,
                    'model_id': assistant.model_id,
                    'temperature': assistant.temperature,
                    'max_tokens': assistant.max_tokens,
                    'context_memory_size': assistant.context_memory_size,
                    'personality_traits': assistant.personality_traits,
                    'response_guidelines': assistant.response_guidelines,
                    'primary_prompt_id': assistant.primary_prompt_id,
                    'prompt_version_id': assistant.prompt_version_id
                },
                resource_allocation=deployment_config or {},
                deployment_logs=[{
                    'timestamp': int(time.time() * 1000),
                    'event': 'deployment_initiated',
                    'message': f'Deployment to {environment} initiated by {user_id}',
                    'details': {'version': assistant.version}
                }]
            )
            
            # Save deployment record
            if self.deployment_repo.create_deployment(deployment):
                # Update assistant status if deploying to production
                if env_enum == DeploymentEnvironment.PRODUCTION:
                    assistant.status = AssistantStatus.ACTIVE
                    assistant.environment = env_enum
                    self.assistant_repo.update(assistant)
                
                # Log deployment analytics
                self.analytics_repo.record_metric(
                    assistant_id,
                    'deployment_count',
                    1.0,
                    'deployment',
                    {'environment': environment, 'version': assistant.version}
                )
                
                return True, deployment
            else:
                return False, "Failed to create deployment record"
                
        except Exception as e:
            logger.error(f"Error deploying assistant {assistant_id} to {environment}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def update_deployment_status(self, deployment_id: int, status: str, user_id: str, 
                                logs: List[Dict[str, Any]] = None) -> tuple[bool, str]:
        """Update deployment status"""
        try:
            # Validate status
            valid_statuses = ['active', 'inactive', 'failed', 'deploying', 'rolling_back']
            if status not in valid_statuses:
                return False, f"Invalid status. Valid options: {', '.join(valid_statuses)}"
            
            # Get deployment
            deployments = self.deployment_repo.get_deployments("")  # This needs to be improved
            deployment = None
            for d in deployments:
                if d.id == deployment_id:
                    deployment = d
                    break
            
            if not deployment:
                return False, "Deployment not found"
            
            # Check permissions (user should be the deployer or assistant owner)
            assistant = self.assistant_repo.get_by_id(deployment.assistant_id)
            if not assistant:
                return False, "Associated assistant not found"
            
            if deployment.deployed_by != user_id and assistant.user_id != user_id:
                return False, "Access denied"
            
            # Update status
            if self.deployment_repo.update_deployment_status(deployment_id, status):
                # Add logs if provided
                if logs:
                    # In a real implementation, we'd update deployment logs
                    pass
                
                # Record analytics
                self.analytics_repo.record_metric(
                    deployment.assistant_id,
                    'deployment_status_change',
                    1.0,
                    'deployment',
                    {'from_status': deployment.status, 'to_status': status, 'environment': deployment.environment.value}
                )
                
                return True, "Deployment status updated successfully"
            else:
                return False, "Failed to update deployment status"
                
        except Exception as e:
            logger.error(f"Error updating deployment status {deployment_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def rollback_deployment(self, assistant_id: str, environment: str, user_id: str, 
                           target_version: Optional[str] = None) -> tuple[bool, str]:
        """Rollback assistant deployment to a previous version"""
        try:
            # Validate environment
            try:
                env_enum = DeploymentEnvironment(environment)
            except ValueError:
                return False, f"Invalid deployment environment: {environment}"
            
            # Get assistant
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            # Check permissions
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Get current active deployment
            current_deployment = self.deployment_repo.get_active_deployment(assistant_id, env_enum)
            if not current_deployment:
                return False, f"No active deployment found in {environment}"
            
            # Get deployment history to find rollback target
            deployments = self.deployment_repo.get_deployments(assistant_id)
            env_deployments = [d for d in deployments if d.environment == env_enum and d.status in ['active', 'inactive']]
            
            if len(env_deployments) < 2:
                return False, "No previous deployment found to rollback to"
            
            # Find target deployment
            target_deployment = None
            if target_version:
                target_deployment = next((d for d in env_deployments if d.version == target_version and d.id != current_deployment.id), None)
            else:
                # Get the most recent deployment before current
                sorted_deployments = sorted([d for d in env_deployments if d.id != current_deployment.id], 
                                          key=lambda x: x.deployed_at, reverse=True)
                if sorted_deployments:
                    target_deployment = sorted_deployments[0]
            
            if not target_deployment:
                version_msg = f" to version {target_version}" if target_version else ""
                return False, f"No suitable deployment found for rollback{version_msg}"
            
            # Mark current deployment as rolling back
            self.deployment_repo.update_deployment_status(current_deployment.id, 'rolling_back')
            
            # Create new deployment with target configuration
            rollback_deployment = AssistantDeployment(
                assistant_id=assistant_id,
                environment=env_enum,
                version=target_deployment.version,
                deployed_by=user_id,
                configuration_snapshot=target_deployment.configuration_snapshot.copy(),
                resource_allocation=target_deployment.resource_allocation.copy(),
                rollback_version=current_deployment.version,
                deployment_logs=[{
                    'timestamp': int(time.time() * 1000),
                    'event': 'rollback_initiated',
                    'message': f'Rollback from {current_deployment.version} to {target_deployment.version}',
                    'details': {
                        'previous_deployment_id': current_deployment.id,
                        'target_deployment_id': target_deployment.id
                    }
                }]
            )
            
            if self.deployment_repo.create_deployment(rollback_deployment):
                # Deactivate current deployment
                self.deployment_repo.update_deployment_status(current_deployment.id, 'inactive')
                
                # Record rollback analytics
                self.analytics_repo.record_metric(
                    assistant_id,
                    'rollback_count',
                    1.0,
                    'deployment',
                    {'environment': environment, 'from_version': current_deployment.version, 'to_version': target_deployment.version}
                )
                
                return True, f"Rollback completed. Assistant rolled back from {current_deployment.version} to {target_deployment.version}"
            else:
                return False, "Failed to create rollback deployment"
                
        except Exception as e:
            logger.error(f"Error rolling back deployment for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_deployment_history(self, assistant_id: str, user_id: str) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get deployment history for an assistant"""
        try:
            # Get assistant and check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Get deployment history
            deployments = self.deployment_repo.get_deployments(assistant_id)
            
            history = []
            for deployment in deployments:
                deployment_data = {
                    'id': deployment.id,
                    'environment': deployment.environment.value,
                    'version': deployment.version,
                    'status': deployment.status,
                    'deployed_at': deployment.deployed_at,
                    'deployed_by': deployment.deployed_by,
                    'rollback_version': deployment.rollback_version,
                    'health_check_url': deployment.health_check_url,
                    'metrics_endpoint': deployment.metrics_endpoint,
                    'configuration_summary': {
                        'model_id': deployment.configuration_snapshot.get('model_id'),
                        'temperature': deployment.configuration_snapshot.get('temperature'),
                        'max_tokens': deployment.configuration_snapshot.get('max_tokens'),
                        'primary_prompt_id': deployment.configuration_snapshot.get('primary_prompt_id')
                    },
                    'resource_allocation': deployment.resource_allocation,
                    'logs_count': len(deployment.deployment_logs)
                }
                history.append(deployment_data)
            
            return True, history
            
        except Exception as e:
            logger.error(f"Error getting deployment history for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_deployment_status(self, assistant_id: str, user_id: str) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get current deployment status across all environments"""
        try:
            # Check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if assistant.user_id != user_id:
                return False, "Access denied"
            
            # Get deployment status from repository view
            status_data = self.assistant_repo.get_deployment_status(assistant_id)
            
            return True, status_data
            
        except Exception as e:
            logger.error(f"Error getting deployment status for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def promote_assistant(self, assistant_id: str, from_env: str, to_env: str, user_id: str) -> tuple[bool, str]:
        """Promote assistant from one environment to another (e.g., staging to production)"""
        try:
            # Validate environments
            try:
                from_env_enum = DeploymentEnvironment(from_env)
                to_env_enum = DeploymentEnvironment(to_env)
            except ValueError as e:
                return False, f"Invalid environment: {str(e)}"
            
            # Validate promotion path
            valid_promotions = {
                DeploymentEnvironment.DEVELOPMENT: [DeploymentEnvironment.TESTING, DeploymentEnvironment.STAGING],
                DeploymentEnvironment.TESTING: [DeploymentEnvironment.STAGING],
                DeploymentEnvironment.STAGING: [DeploymentEnvironment.PRODUCTION]
            }
            
            if to_env_enum not in valid_promotions.get(from_env_enum, []):
                return False, f"Invalid promotion path from {from_env} to {to_env}"
            
            # Get source deployment
            source_deployment = self.deployment_repo.get_active_deployment(assistant_id, from_env_enum)
            if not source_deployment:
                return False, f"No active deployment found in {from_env}"
            
            # Check if assistant meets promotion criteria
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            can_deploy, reason = assistant.can_deploy_to(to_env_enum)
            if not can_deploy:
                return False, f"Assistant cannot be promoted: {reason}"
            
            # Deploy to target environment using source configuration
            success, result = self.deploy_assistant(
                assistant_id, 
                to_env, 
                user_id,
                source_deployment.resource_allocation
            )
            
            if success:
                # Record promotion analytics
                self.analytics_repo.record_metric(
                    assistant_id,
                    'promotion_count',
                    1.0,
                    'deployment',
                    {'from_environment': from_env, 'to_environment': to_env, 'version': source_deployment.version}
                )
                
                return True, f"Assistant successfully promoted from {from_env} to {to_env}"
            else:
                return False, f"Promotion failed: {result}"
                
        except Exception as e:
            logger.error(f"Error promoting assistant {assistant_id} from {from_env} to {to_env}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def scale_deployment(self, assistant_id: str, environment: str, user_id: str, 
                        resource_config: Dict[str, Any]) -> tuple[bool, str]:
        """Scale deployment resources"""
        try:
            # Validate environment
            try:
                env_enum = DeploymentEnvironment(environment)
            except ValueError:
                return False, f"Invalid deployment environment: {environment}"
            
            # Get active deployment
            deployment = self.deployment_repo.get_active_deployment(assistant_id, env_enum)
            if not deployment:
                return False, f"No active deployment found in {environment}"
            
            # Check permissions
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant or assistant.user_id != user_id:
                return False, "Access denied"
            
            # Update resource allocation (this would integrate with actual orchestration system)
            updated_resources = deployment.resource_allocation.copy()
            updated_resources.update(resource_config)
            
            # In a real implementation, this would call the orchestration system (K8s, Docker Swarm, etc.)
            # For now, we'll just update the record
            
            # Record scaling event
            self.analytics_repo.record_metric(
                assistant_id,
                'scaling_event',
                1.0,
                'deployment',
                {'environment': environment, 'resource_changes': resource_config}
            )
            
            return True, "Deployment scaled successfully"
            
        except Exception as e:
            logger.error(f"Error scaling deployment for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"


# Initialize service
deployment_service = DeploymentService()


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
@deployment_bp.route('/<assistant_id>/deploy', methods=['POST'])
@require_user_id
def deploy_assistant(assistant_id: str):
    """Deploy an assistant to a specific environment"""
    try:
        data = request.get_json()
        if not data or 'environment' not in data:
            return jsonify({'error': 'environment is required'}), 400
        
        environment = data['environment']
        deployment_config = data.get('deployment_config', {})
        
        success, result = deployment_service.deploy_assistant(
            assistant_id, environment, g.user_id, deployment_config
        )
        
        if success:
            deployment = result
            return jsonify({
                'message': 'Assistant deployed successfully',
                'deployment': {
                    'id': deployment.id,
                    'environment': deployment.environment.value,
                    'version': deployment.version,
                    'status': deployment.status,
                    'deployed_at': deployment.deployed_at,
                    'health_check_url': deployment.health_check_url,
                    'metrics_endpoint': deployment.metrics_endpoint
                }
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in deploy_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/deployments/<int:deployment_id>/status', methods=['PUT'])
@require_user_id
def update_deployment_status(deployment_id: int):
    """Update deployment status"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'status is required'}), 400
        
        status = data['status']
        logs = data.get('logs', [])
        
        success, result = deployment_service.update_deployment_status(
            deployment_id, status, g.user_id, logs
        )
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in update_deployment_status endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/<assistant_id>/rollback', methods=['POST'])
@require_user_id
def rollback_deployment(assistant_id: str):
    """Rollback assistant deployment"""
    try:
        data = request.get_json()
        if not data or 'environment' not in data:
            return jsonify({'error': 'environment is required'}), 400
        
        environment = data['environment']
        target_version = data.get('target_version')
        
        success, result = deployment_service.rollback_deployment(
            assistant_id, environment, g.user_id, target_version
        )
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in rollback_deployment endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/<assistant_id>/deployments', methods=['GET'])
@require_user_id
def get_deployment_history(assistant_id: str):
    """Get deployment history for an assistant"""
    try:
        success, result = deployment_service.get_deployment_history(assistant_id, g.user_id)
        
        if success:
            return jsonify({'deployments': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_deployment_history endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/<assistant_id>/deployment-status', methods=['GET'])
@require_user_id
def get_deployment_status(assistant_id: str):
    """Get current deployment status across all environments"""
    try:
        success, result = deployment_service.get_deployment_status(assistant_id, g.user_id)
        
        if success:
            return jsonify({'status': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_deployment_status endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/<assistant_id>/promote', methods=['POST'])
@require_user_id
def promote_assistant(assistant_id: str):
    """Promote assistant from one environment to another"""
    try:
        data = request.get_json()
        if not data or 'from_environment' not in data or 'to_environment' not in data:
            return jsonify({'error': 'from_environment and to_environment are required'}), 400
        
        from_env = data['from_environment']
        to_env = data['to_environment']
        
        success, result = deployment_service.promote_assistant(
            assistant_id, from_env, to_env, g.user_id
        )
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in promote_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/<assistant_id>/scale', methods=['POST'])
@require_user_id
def scale_deployment(assistant_id: str):
    """Scale deployment resources"""
    try:
        data = request.get_json()
        if not data or 'environment' not in data or 'resource_config' not in data:
            return jsonify({'error': 'environment and resource_config are required'}), 400
        
        environment = data['environment']
        resource_config = data['resource_config']
        
        success, result = deployment_service.scale_deployment(
            assistant_id, environment, g.user_id, resource_config
        )
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in scale_deployment endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@deployment_bp.route('/environments', methods=['GET'])
def get_deployment_environments():
    """Get available deployment environments"""
    try:
        environments = [
            {
                'value': env.value, 
                'name': env.value.replace('_', ' ').title(),
                'description': {
                    'development': 'Local development and testing',
                    'testing': 'Automated testing and QA',
                    'staging': 'Pre-production testing with production-like data',
                    'production': 'Live production environment'
                }.get(env.value, 'Environment description')
            } 
            for env in DeploymentEnvironment
        ]
        return jsonify({'environments': environments}), 200
    except Exception as e:
        logger.error(f"Error in get_deployment_environments endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500