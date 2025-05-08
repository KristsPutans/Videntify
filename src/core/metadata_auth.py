"""Authentication Integration for Metadata Enrichment

This module provides authentication and authorization mechanisms
for securing the metadata enrichment process based on user permissions.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for metadata access."""
    NONE = "none"                # No access
    BASIC = "basic"              # Basic metadata only
    STANDARD = "standard"        # Standard metadata
    ENHANCED = "enhanced"        # Enhanced metadata including external API data
    ADMIN = "admin"              # Full administrative access


class UserRole(str, Enum):
    """User roles for authentication."""
    GUEST = "guest"              # Guest user with minimal permissions
    USER = "user"                # Regular authenticated user
    PREMIUM = "premium"          # Premium user with additional permissions
    STAFF = "staff"              # Staff member with elevated permissions
    ADMIN = "admin"              # Administrator with full access


class MetadataScope(str, Enum):
    """Scopes for metadata access."""
    PUBLIC = "public"            # Publicly available metadata
    BASIC_INFO = "basic_info"    # Basic information like title, year
    EXTERNAL_API = "external_api" # Data from external APIs (TMDB, YouTube, etc.)
    SENSITIVE = "sensitive"      # Sensitive/premium metadata
    ADMIN = "admin"              # Administrative level metadata


class AuthConfig(BaseModel):
    """Configuration for metadata authentication."""
    enable_auth: bool = True
    default_role: UserRole = UserRole.GUEST
    token_expiry_seconds: int = 3600
    role_permissions: Dict[UserRole, List[MetadataScope]] = Field(default_factory=dict)
    api_key_header: str = "X-API-Key"
    auth_token_header: str = "Authorization"
    
    class Config:
        arbitrary_types_allowed = True


class UserInfo(BaseModel):
    """User information for authentication."""
    user_id: str
    username: str
    role: UserRole
    scopes: List[MetadataScope] = Field(default_factory=list)
    api_keys: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class MetadataAuthManager:
    """Manager for metadata authentication and authorization."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the auth manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = AuthConfig(**config.get("auth", {}))
        self.users: Dict[str, UserInfo] = {}
        self.api_keys: Dict[str, str] = {}  # API key to user_id mapping
        self.tokens: Dict[str, Dict[str, Any]] = {}  # Token to user_session mapping
        
        # Default role permissions if not specified
        if not self.config.role_permissions:
            self.config.role_permissions = {
                UserRole.GUEST: [MetadataScope.PUBLIC],
                UserRole.USER: [MetadataScope.PUBLIC, MetadataScope.BASIC_INFO],
                UserRole.PREMIUM: [MetadataScope.PUBLIC, MetadataScope.BASIC_INFO, MetadataScope.EXTERNAL_API],
                UserRole.STAFF: [MetadataScope.PUBLIC, MetadataScope.BASIC_INFO, MetadataScope.EXTERNAL_API, MetadataScope.SENSITIVE],
                UserRole.ADMIN: [MetadataScope.PUBLIC, MetadataScope.BASIC_INFO, MetadataScope.EXTERNAL_API, MetadataScope.SENSITIVE, MetadataScope.ADMIN]
            }
            
        # Load users from config
        self._load_users(config.get("users", []))
        
        logger.info(f"Initialized MetadataAuthManager with {len(self.users)} users")
    
    def _load_users(self, user_configs: List[Dict[str, Any]]):
        """Load user configurations."""
        for user_config in user_configs:
            user_id = user_config.get("user_id")
            if not user_id:
                continue
                
            # Create user info
            user_info = UserInfo(
                user_id=user_id,
                username=user_config.get("username", f"user_{user_id}"),
                role=UserRole(user_config.get("role", self.config.default_role.value)),
                api_keys=user_config.get("api_keys", [])
            )
            
            # Set scopes based on role if not explicitly provided
            if "scopes" in user_config:
                user_info.scopes = [MetadataScope(s) for s in user_config["scopes"]]
            else:
                role_scopes = self.config.role_permissions.get(user_info.role, [])
                user_info.scopes = role_scopes
                
            # Add user to the users dict
            self.users[user_id] = user_info
            
            # Map API keys to user_id
            for api_key in user_info.api_keys:
                self.api_keys[api_key] = user_id
    
    def authenticate(self, auth_header: Optional[str] = None, api_key_header: Optional[str] = None) -> Optional[UserInfo]:
        """Authenticate a user from request headers.
        
        Args:
            auth_header: Authorization header value
            api_key_header: API key header value
            
        Returns:
            UserInfo if authenticated, None otherwise
        """
        if not self.config.enable_auth:
            # Create a default admin user if auth is disabled
            return UserInfo(
                user_id="system",
                username="system",
                role=UserRole.ADMIN,
                scopes=list(MetadataScope)
            )
            
        # Try API key first
        if api_key_header:
            user_id = self.api_keys.get(api_key_header)
            if user_id and user_id in self.users:
                return self.users[user_id]
                
        # Try auth token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            token_data = self.tokens.get(token)
            
            if token_data:
                # Check if token is expired
                if token_data.get("expires_at", 0) > time.time():
                    user_id = token_data.get("user_id")
                    if user_id and user_id in self.users:
                        # Update last access time
                        self.tokens[token]["last_access"] = time.time()
                        return self.users[user_id]
                else:
                    # Token expired, remove it
                    del self.tokens[token]
                    
        # Return guest user by default
        if "guest" in self.users:
            return self.users["guest"]
            
        # Create a new guest user if none exists
        guest_user = UserInfo(
            user_id="guest",
            username="guest",
            role=UserRole.GUEST,
            scopes=self.config.role_permissions.get(UserRole.GUEST, [])
        )
        self.users["guest"] = guest_user
        return guest_user
    
    def has_permission(self, user: UserInfo, required_scope: MetadataScope) -> bool:
        """Check if a user has permission for a scope.
        
        Args:
            user: User to check
            required_scope: Required scope
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.config.enable_auth:
            return True
            
        return required_scope in user.scopes
    
    def filter_metadata_fields(self, metadata: Dict[str, Any], user: UserInfo) -> Dict[str, Any]:
        """Filter metadata fields based on user permissions.
        
        Args:
            metadata: Metadata to filter
            user: User to filter for
            
        Returns:
            Filtered metadata
        """
        if not self.config.enable_auth:
            return metadata
        
        # Import our field permissions system
        # Importing here to avoid circular imports
        from src.core.metadata_field_permissions import get_field_scope
            
        # Get all user's accessible scopes
        user_scopes = set(user.scopes)
        
        # Filter the metadata based on field permissions
        filtered_metadata = {}
        for field, value in metadata.items():
            # Special case for core fields that should always be included
            if field in ["content_id", "title"]:
                filtered_metadata[field] = value
                continue
                
            # Get the required scope for this field
            required_scope = get_field_scope(field)
            
            # Include field if user has the required scope
            if required_scope in user_scopes:
                filtered_metadata[field] = value
                
        # Always include content type if available as it's needed for UI rendering
        if "content_type" in metadata and "content_type" not in filtered_metadata:
            filtered_metadata["content_type"] = metadata["content_type"]
                
        return filtered_metadata
    
    def create_auth_token(self, user_id: str) -> Optional[str]:
        """Create an authentication token for a user.
        
        Args:
            user_id: User ID to create token for
            
        Returns:
            Authentication token
        """
        if user_id not in self.users:
            return None
            
        # Create a simple token (in a real system, use a proper JWT)
        import uuid
        token = str(uuid.uuid4())
        
        # Store token data
        self.tokens[token] = {
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + self.config.token_expiry_seconds,
            "last_access": time.time()
        }
        
        return token
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token.
        
        Args:
            token: Token to invalidate
            
        Returns:
            True if token was found and invalidated, False otherwise
        """
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def clean_expired_tokens(self):
        """Clean expired tokens."""
        current_time = time.time()
        expired_tokens = []
        
        for token, data in self.tokens.items():
            if data.get("expires_at", 0) < current_time:
                expired_tokens.append(token)
                
        for token in expired_tokens:
            del self.tokens[token]
            
        if expired_tokens:
            logger.debug(f"Cleaned {len(expired_tokens)} expired tokens")
    
    def add_user(self, user_info: UserInfo):
        """Add a new user.
        
        Args:
            user_info: User information
        """
        self.users[user_info.user_id] = user_info
        
        # Map API keys to user_id
        for api_key in user_info.api_keys:
            self.api_keys[api_key] = user_info.user_id
            
    def remove_user(self, user_id: str) -> bool:
        """Remove a user.
        
        Args:
            user_id: User ID to remove
            
        Returns:
            True if user was found and removed, False otherwise
        """
        if user_id in self.users:
            user = self.users[user_id]
            
            # Remove API key mappings
            for api_key in user.api_keys:
                if api_key in self.api_keys:
                    del self.api_keys[api_key]
                    
            # Remove token mappings
            tokens_to_remove = []
            for token, data in self.tokens.items():
                if data.get("user_id") == user_id:
                    tokens_to_remove.append(token)
                    
            for token in tokens_to_remove:
                del self.tokens[token]
                
            # Remove user
            del self.users[user_id]
            return True
            
        return False
        
    def filter_metadata_sources(self, sources: List[Dict[str, Any]], user: UserInfo) -> List[Dict[str, Any]]:
        """Filter metadata sources based on user permissions.
        
        Args:
            sources: List of metadata sources
            user: User to filter for
            
        Returns:
            Filtered list of metadata sources
        """
        if not self.config.enable_auth:
            return sources
            
        user_scopes = set(user.scopes)
        filtered_sources = []
        
        # Source type to scope mapping
        source_to_scope = {
            "file": MetadataScope.PUBLIC,
            "local_db": MetadataScope.BASIC_INFO,
            "tmdb": MetadataScope.EXTERNAL_API,
            "youtube": MetadataScope.EXTERNAL_API,
            "spotify": MetadataScope.SENSITIVE,
            "wikipedia": MetadataScope.EXTERNAL_API,
            "location": MetadataScope.SENSITIVE,
            "content_analysis": MetadataScope.EXTERNAL_API
        }
        
        for source in sources:
            source_type = source.get("type")
            required_scope = source_to_scope.get(source_type, MetadataScope.ADMIN)
            
            if required_scope in user_scopes:
                filtered_sources.append(source)
                
        return filtered_sources
        
    def get_guest_user(self) -> UserInfo:
        """Get the guest user or create one if it doesn't exist.
        
        Returns:
            Guest user info
        """
        if "guest" in self.users:
            return self.users["guest"]
            
        # Create a new guest user
        guest_user = UserInfo(
            user_id="guest",
            username="guest",
            role=UserRole.GUEST,
            scopes=self.config.role_permissions.get(UserRole.GUEST, [MetadataScope.PUBLIC])
        )
        self.users["guest"] = guest_user
        return guest_user
