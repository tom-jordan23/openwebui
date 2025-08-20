"""
Enterprise Authentication and SSO Integration
Supports SAML, OIDC, LDAP, and multi-factor authentication
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import jwt
import hashlib
import secrets
from urllib.parse import urlencode, parse_qs

# SAML and OIDC libraries
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False

try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False

try:
    import pyotp
    import qrcode
    MFA_AVAILABLE = True
except ImportError:
    MFA_AVAILABLE = False

logger = logging.getLogger(__name__)


class AuthenticationMethod(Enum):
    """Supported authentication methods"""
    LOCAL = "local"
    SAML = "saml"
    OIDC = "oidc"
    LDAP = "ldap"
    OAUTH2 = "oauth2"


class UserRole(Enum):
    """User roles for RBAC"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER_ADMIN = "user_admin"
    POWER_USER = "power_user"
    STANDARD_USER = "standard_user"
    READ_ONLY = "read_only"
    GUEST = "guest"


class MFAType(Enum):
    """Multi-factor authentication types"""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_TOKEN = "hardware_token"
    PUSH_NOTIFICATION = "push_notification"


@dataclass
class UserProfile:
    """Enterprise user profile"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    tenant_id: str
    roles: List[UserRole]
    groups: List[str]
    authentication_method: AuthenticationMethod
    mfa_enabled: bool
    mfa_methods: List[MFAType]
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    is_active: bool = True
    password_expires_at: Optional[datetime] = None
    account_locked: bool = False
    failed_login_attempts: int = 0


@dataclass
class TenantConfiguration:
    """Multi-tenant configuration"""
    tenant_id: str
    name: str
    domain: str
    authentication_methods: List[AuthenticationMethod]
    sso_configuration: Dict[str, Any]
    branding: Dict[str, Any]
    settings: Dict[str, Any]
    resource_limits: Dict[str, Any]
    created_at: datetime
    is_active: bool = True


@dataclass
class AuthenticationResult:
    """Authentication operation result"""
    success: bool
    user_profile: Optional[UserProfile]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: int
    error_message: Optional[str] = None
    requires_mfa: bool = False
    mfa_challenge: Optional[Dict[str, Any]] = None


class EnterpriseAuthenticationManager:
    """Enterprise authentication and SSO management"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30
        
        # Initialize authentication providers
        self.saml_provider = SAMLProvider() if SAML_AVAILABLE else None
        self.oidc_provider = OIDCProvider()
        self.ldap_provider = LDAPProvider() if LDAP_AVAILABLE else None
        self.local_provider = LocalAuthProvider()
        self.mfa_provider = MFAProvider() if MFA_AVAILABLE else None
        
        # In-memory storage for demo (use database in production)
        self.users = {}
        self.tenants = {}
        self.sessions = {}
        
        # Initialize default tenant
        self._initialize_default_tenant()
    
    def _initialize_default_tenant(self):
        """Initialize default tenant configuration"""
        default_tenant = TenantConfiguration(
            tenant_id="default",
            name="Default Organization",
            domain="localhost",
            authentication_methods=[AuthenticationMethod.LOCAL, AuthenticationMethod.SAML],
            sso_configuration={},
            branding={
                'logo_url': '/static/logo.png',
                'primary_color': '#007bff',
                'company_name': 'OpenWebUI'
            },
            settings={
                'password_policy': {
                    'min_length': 8,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_symbols': False,
                    'password_expiry_days': 90
                },
                'session_timeout_minutes': 480,  # 8 hours
                'max_failed_login_attempts': 5,
                'account_lockout_duration_minutes': 30
            },
            resource_limits={
                'max_users': 1000,
                'max_conversations_per_user': 100,
                'max_storage_gb': 100
            },
            created_at=datetime.now()
        )
        
        self.tenants["default"] = default_tenant
    
    async def authenticate_user(self, credentials: Dict[str, Any], 
                              tenant_id: str = "default") -> AuthenticationResult:
        """Authenticate user with various methods"""
        try:
            tenant = self.tenants.get(tenant_id)
            if not tenant or not tenant.is_active:
                return AuthenticationResult(
                    success=False,
                    user_profile=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    error_message="Invalid tenant"
                )
            
            auth_method = credentials.get('method', AuthenticationMethod.LOCAL)
            
            # Route to appropriate authentication provider
            if auth_method == AuthenticationMethod.LOCAL:
                result = await self.local_provider.authenticate(credentials)
            elif auth_method == AuthenticationMethod.SAML and self.saml_provider:
                result = await self.saml_provider.authenticate(credentials, tenant)
            elif auth_method == AuthenticationMethod.OIDC:
                result = await self.oidc_provider.authenticate(credentials, tenant)
            elif auth_method == AuthenticationMethod.LDAP and self.ldap_provider:
                result = await self.ldap_provider.authenticate(credentials, tenant)
            else:
                return AuthenticationResult(
                    success=False,
                    user_profile=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    error_message=f"Authentication method {auth_method} not supported"
                )
            
            if not result.success:
                await self._handle_failed_login(credentials.get('email', ''), tenant_id)
                return result
            
            # Check if MFA is required
            if result.user_profile and result.user_profile.mfa_enabled:
                if not credentials.get('mfa_code'):
                    mfa_challenge = await self._generate_mfa_challenge(result.user_profile)
                    return AuthenticationResult(
                        success=False,
                        user_profile=result.user_profile,
                        access_token=None,
                        refresh_token=None,
                        expires_in=0,
                        requires_mfa=True,
                        mfa_challenge=mfa_challenge
                    )
                else:
                    # Verify MFA code
                    mfa_valid = await self._verify_mfa_code(
                        result.user_profile, credentials.get('mfa_code')
                    )
                    if not mfa_valid:
                        return AuthenticationResult(
                            success=False,
                            user_profile=None,
                            access_token=None,
                            refresh_token=None,
                            expires_in=0,
                            error_message="Invalid MFA code"
                        )
            
            # Generate tokens
            access_token = await self._generate_access_token(result.user_profile, tenant_id)
            refresh_token = await self._generate_refresh_token(result.user_profile, tenant_id)
            
            # Update user login information
            result.user_profile.last_login = datetime.now()
            result.user_profile.failed_login_attempts = 0
            result.user_profile.account_locked = False
            
            # Store session
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                'user_id': result.user_profile.user_id,
                'tenant_id': tenant_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
            return AuthenticationResult(
                success=True,
                user_profile=result.user_profile,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message=str(e)
            )
    
    async def _generate_access_token(self, user_profile: UserProfile, tenant_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            'user_id': user_profile.user_id,
            'email': user_profile.email,
            'tenant_id': tenant_id,
            'roles': [role.value for role in user_profile.roles],
            'groups': user_profile.groups,
            'exp': datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def _generate_refresh_token(self, user_profile: UserProfile, tenant_id: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            'user_id': user_profile.user_id,
            'tenant_id': tenant_id,
            'exp': datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return False, {'error': 'Invalid token'}
    
    async def refresh_access_token(self, refresh_token: str) -> AuthenticationResult:
        """Refresh access token using refresh token"""
        valid, payload = await self.verify_token(refresh_token)
        
        if not valid or payload.get('type') != 'refresh':
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="Invalid refresh token"
            )
        
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        
        # Get user profile
        user_profile = self.users.get(user_id)
        if not user_profile or not user_profile.is_active:
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="User not found or inactive"
            )
        
        # Generate new access token
        new_access_token = await self._generate_access_token(user_profile, tenant_id)
        
        return AuthenticationResult(
            success=True,
            user_profile=user_profile,
            access_token=new_access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            expires_in=self.access_token_expire_minutes * 60
        )
    
    async def setup_mfa(self, user_id: str, mfa_type: MFAType) -> Dict[str, Any]:
        """Set up multi-factor authentication for user"""
        if not self.mfa_provider:
            raise ValueError("MFA not available")
        
        user_profile = self.users.get(user_id)
        if not user_profile:
            raise ValueError("User not found")
        
        return await self.mfa_provider.setup_mfa(user_profile, mfa_type)
    
    async def _generate_mfa_challenge(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate MFA challenge for user"""
        if not self.mfa_provider:
            return {}
        
        return await self.mfa_provider.generate_challenge(user_profile)
    
    async def _verify_mfa_code(self, user_profile: UserProfile, mfa_code: str) -> bool:
        """Verify MFA code"""
        if not self.mfa_provider:
            return True  # Skip MFA if not available
        
        return await self.mfa_provider.verify_code(user_profile, mfa_code)
    
    async def _handle_failed_login(self, email: str, tenant_id: str):
        """Handle failed login attempt"""
        # Find user by email
        user_profile = None
        for user in self.users.values():
            if user.email == email and user.tenant_id == tenant_id:
                user_profile = user
                break
        
        if user_profile:
            user_profile.failed_login_attempts += 1
            
            tenant = self.tenants.get(tenant_id)
            max_attempts = tenant.settings.get('max_failed_login_attempts', 5)
            
            if user_profile.failed_login_attempts >= max_attempts:
                user_profile.account_locked = True
                logger.warning(f"Account locked for user {email} due to too many failed attempts")
    
    async def create_tenant(self, tenant_config: TenantConfiguration) -> bool:
        """Create new tenant"""
        try:
            self.tenants[tenant_config.tenant_id] = tenant_config
            logger.info(f"Created tenant: {tenant_config.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str, resource: str) -> List[str]:
        """Get user permissions for a resource"""
        user_profile = self.users.get(user_id)
        if not user_profile:
            return []
        
        permissions = []
        
        # Role-based permissions
        for role in user_profile.roles:
            permissions.extend(self._get_role_permissions(role, resource))
        
        # Group-based permissions
        for group in user_profile.groups:
            permissions.extend(self._get_group_permissions(group, resource))
        
        return list(set(permissions))  # Remove duplicates
    
    def _get_role_permissions(self, role: UserRole, resource: str) -> List[str]:
        """Get permissions for a role"""
        role_permissions = {
            UserRole.SUPER_ADMIN: ['*'],  # All permissions
            UserRole.TENANT_ADMIN: ['tenant:*', 'user:*', 'config:*'],
            UserRole.USER_ADMIN: ['user:read', 'user:create', 'user:update'],
            UserRole.POWER_USER: ['conversation:*', 'model:use', 'export:own'],
            UserRole.STANDARD_USER: ['conversation:own', 'model:use'],
            UserRole.READ_ONLY: ['conversation:read', 'model:read'],
            UserRole.GUEST: ['conversation:read']
        }
        
        permissions = role_permissions.get(role, [])
        
        # Filter by resource if not wildcard
        if '*' not in permissions:
            permissions = [p for p in permissions if p.startswith(resource + ':') or p.endswith(':*')]
        
        return permissions
    
    def _get_group_permissions(self, group: str, resource: str) -> List[str]:
        """Get permissions for a group"""
        # This would typically be configured per tenant
        group_permissions = {
            'developers': ['conversation:*', 'model:*', 'debug:*'],
            'analysts': ['conversation:read', 'model:use', 'export:*'],
            'managers': ['conversation:read', 'user:read', 'analytics:read']
        }
        
        return group_permissions.get(group, [])


class LocalAuthProvider:
    """Local username/password authentication"""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """Authenticate using local credentials"""
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="Email and password required"
            )
        
        # This would typically check against a database
        # For demo, create a mock user
        user_profile = UserProfile(
            user_id="user_123",
            email=email,
            first_name="Demo",
            last_name="User",
            display_name="Demo User",
            tenant_id="default",
            roles=[UserRole.STANDARD_USER],
            groups=["users"],
            authentication_method=AuthenticationMethod.LOCAL,
            mfa_enabled=False,
            mfa_methods=[],
            last_login=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )
        
        return AuthenticationResult(
            success=True,
            user_profile=user_profile,
            access_token=None,
            refresh_token=None,
            expires_in=0
        )


class SAMLProvider:
    """SAML SSO authentication provider"""
    
    def __init__(self):
        self.settings = {
            # SAML settings would be loaded from configuration
        }
    
    async def authenticate(self, credentials: Dict[str, Any], 
                          tenant: TenantConfiguration) -> AuthenticationResult:
        """Authenticate using SAML"""
        # This would implement actual SAML authentication
        # For now, return a mock result
        
        saml_response = credentials.get('saml_response')
        if not saml_response:
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="SAML response required"
            )
        
        # Mock SAML user
        user_profile = UserProfile(
            user_id="saml_user_456",
            email="user@example.com",
            first_name="SAML",
            last_name="User",
            display_name="SAML User",
            tenant_id=tenant.tenant_id,
            roles=[UserRole.STANDARD_USER],
            groups=["saml_users"],
            authentication_method=AuthenticationMethod.SAML,
            mfa_enabled=True,
            mfa_methods=[MFAType.TOTP],
            last_login=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={'saml_attributes': {}}
        )
        
        return AuthenticationResult(
            success=True,
            user_profile=user_profile,
            access_token=None,
            refresh_token=None,
            expires_in=0
        )


class OIDCProvider:
    """OpenID Connect authentication provider"""
    
    async def authenticate(self, credentials: Dict[str, Any], 
                          tenant: TenantConfiguration) -> AuthenticationResult:
        """Authenticate using OIDC"""
        # This would implement actual OIDC authentication
        # For now, return a mock result
        
        return AuthenticationResult(
            success=True,
            user_profile=None,
            access_token=None,
            refresh_token=None,
            expires_in=0
        )


class LDAPProvider:
    """LDAP/Active Directory authentication provider"""
    
    def __init__(self):
        self.server_url = os.getenv('LDAP_SERVER_URL', 'ldap://localhost:389')
        self.bind_dn = os.getenv('LDAP_BIND_DN', '')
        self.bind_password = os.getenv('LDAP_BIND_PASSWORD', '')
        self.user_base_dn = os.getenv('LDAP_USER_BASE_DN', 'ou=users,dc=example,dc=com')
    
    async def authenticate(self, credentials: Dict[str, Any], 
                          tenant: TenantConfiguration) -> AuthenticationResult:
        """Authenticate using LDAP"""
        if not LDAP_AVAILABLE:
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="LDAP not available"
            )
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return AuthenticationResult(
                success=False,
                user_profile=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                error_message="Username and password required"
            )
        
        # This would implement actual LDAP authentication
        # For now, return a mock result
        
        user_profile = UserProfile(
            user_id=f"ldap_{username}",
            email=f"{username}@example.com",
            first_name="LDAP",
            last_name="User",
            display_name=f"LDAP {username}",
            tenant_id=tenant.tenant_id,
            roles=[UserRole.STANDARD_USER],
            groups=["ldap_users"],
            authentication_method=AuthenticationMethod.LDAP,
            mfa_enabled=False,
            mfa_methods=[],
            last_login=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={'ldap_dn': f"uid={username},{self.user_base_dn}"}
        )
        
        return AuthenticationResult(
            success=True,
            user_profile=user_profile,
            access_token=None,
            refresh_token=None,
            expires_in=0
        )


class MFAProvider:
    """Multi-factor authentication provider"""
    
    def __init__(self):
        self.mfa_secrets = {}  # In production, store in secure database
    
    async def setup_mfa(self, user_profile: UserProfile, mfa_type: MFAType) -> Dict[str, Any]:
        """Set up MFA for user"""
        if not MFA_AVAILABLE:
            raise ValueError("MFA libraries not available")
        
        if mfa_type == MFAType.TOTP:
            # Generate TOTP secret
            secret = pyotp.random_base32()
            self.mfa_secrets[user_profile.user_id] = secret
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_profile.email,
                issuer_name="OpenWebUI"
            )
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            return {
                'mfa_type': mfa_type.value,
                'secret': secret,
                'provisioning_uri': provisioning_uri,
                'backup_codes': self._generate_backup_codes()
            }
        
        elif mfa_type == MFAType.SMS:
            # SMS setup would integrate with SMS provider
            return {
                'mfa_type': mfa_type.value,
                'phone_number': user_profile.metadata.get('phone_number'),
                'setup_required': True
            }
        
        else:
            raise ValueError(f"MFA type {mfa_type} not supported")
    
    async def generate_challenge(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate MFA challenge"""
        if MFAType.TOTP in user_profile.mfa_methods:
            return {
                'type': MFAType.TOTP.value,
                'message': 'Enter the 6-digit code from your authenticator app'
            }
        
        elif MFAType.SMS in user_profile.mfa_methods:
            # Send SMS code
            code = secrets.randbelow(999999)
            # In production, send via SMS provider
            return {
                'type': MFAType.SMS.value,
                'message': f'SMS code sent to {user_profile.metadata.get("phone_number", "***-***-****")}'
            }
        
        return {}
    
    async def verify_code(self, user_profile: UserProfile, code: str) -> bool:
        """Verify MFA code"""
        if not MFA_AVAILABLE:
            return True  # Skip if not available
        
        if MFAType.TOTP in user_profile.mfa_methods:
            secret = self.mfa_secrets.get(user_profile.user_id)
            if secret:
                totp = pyotp.TOTP(secret)
                return totp.verify(code)
        
        elif MFAType.SMS in user_profile.mfa_methods:
            # Verify SMS code (would check against sent code)
            return len(code) == 6 and code.isdigit()
        
        return False
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes for MFA recovery"""
        return [secrets.token_hex(4).upper() for _ in range(10)]