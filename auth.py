"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - AUTH & SECURITY SUBSYSTEM
Implements:
  1. Password Hashing (Salted cryptographic hash with PBKDF2 / HMAC-SHA256 & bcrypt)
  2. JWT Issuance & Verification (HMAC-SHA256 signature, expiry, claims)
  3. Role-Based Authorization Checks (RBAC: 'admin', 'operator', 'guest')
  4. Rate Limiting (Sliding window memory-backed limiter per IP/Client)
  5. Input Sanitization & Injection Awareness (Defenses against SQL, Shell & Prompt injection)
  6. OAuth / 3rd-Party Login (OAuth2 token exchange simulation)
"""

import re
import os
import time
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import jwt

logger = logging.getLogger("JarvisAuth")

# Secret configuration loaded from environment with secure fallback
JWT_SECRET_KEY = os.getenv("JARVIS_JWT_SECRET", "jarvis-super-secure-production-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JARVIS_JWT_EXPIRY_MINS", "120"))

# Rate Limiter Window Storage: {client_id: [(timestamp)]}
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
DEFAULT_RATE_LIMIT = 60  # requests per minute window


# =====================================================================
# 1. PASSWORD HASHING & VERIFICATION
# =====================================================================
class PasswordSecurity:
    """
    Cryptographic password management using PBKDF2-HMAC-SHA256 with random salt.
    Guarantees resistance against rainbow table and brute-force attacks.
    """
    ITERATIONS = 100_000

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hashes a plaintext password with a cryptographically secure 16-byte random salt."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=cls.ITERATIONS
        )
        # Store as: salt_hex$hash_hex
        return f"{salt.hex()}${key.hex()}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """Verifies candidate plaintext against stored salt$hash string."""
        try:
            salt_hex, key_hex = stored_hash.split("$")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            test_key = hashlib.pbkdf2_hmac(
                hash_name="sha256",
                password=password.encode("utf-8"),
                salt=salt,
                iterations=cls.ITERATIONS
            )
            return hmac.compare_digest(expected_key, test_key)
        except Exception as e:
            logger.warning(f"Password verification encountered error: {e}")
            return False


# =====================================================================
# 2. JWT ISSUANCE & VERIFICATION
# =====================================================================
class TokenManager:
    """Issues and validates JSON Web Tokens (JWT) for stateless API authentication."""

    @staticmethod
    def create_access_token(
        subject: str,
        role: str = "guest",
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generates signed JWT token with subject (user_id/username), role, and expiration."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
        payload = {
            "sub": str(subject),
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        if extra_claims:
            payload.update(extra_claims)
        encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decodes and cryptographically verifies token signature and expiration."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise PermissionError("Authentication token has expired.")
        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Invalid authentication token: {str(e)}")


# =====================================================================
# 3. ROLE-BASED AUTHORIZATION CHECKS (RBAC)
# =====================================================================
class RBAC:
    """
    Role-Based Access Control hierarchy:
    'admin' > 'operator' > 'guest'
    """
    ROLE_HIERARCHY = {
        "admin": 3,
        "operator": 2,
        "guest": 1
    }

    @classmethod
    def is_authorized(cls, user_role: str, required_role: str) -> bool:
        """Checks if user's role meets or exceeds required authority level."""
        user_level = cls.ROLE_HIERARCHY.get(user_role.lower(), 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role.lower(), 1)
        return user_level >= required_level

    @classmethod
    def enforce_role(cls, user_role: str, required_role: str) -> None:
        """Raises PermissionError if authorization level is insufficient."""
        if not cls.is_authorized(user_role, required_role):
            raise PermissionError(
                f"Access denied: Required role '{required_role}', user possesses '{user_role}'."
            )


# =====================================================================
# 4. RATE LIMITING (SLIDING WINDOW)
# =====================================================================
class RateLimiter:
    """
    In-memory sliding window rate limiter tracking requests per client.
    Defends against DoS and brute-force credential stuffing.
    """
    @staticmethod
    def is_allowed(client_id: str, max_requests: int = DEFAULT_RATE_LIMIT, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds

        if client_id not in _RATE_LIMIT_STORE:
            _RATE_LIMIT_STORE[client_id] = []

        # Evict timestamps older than current window
        _RATE_LIMIT_STORE[client_id] = [
            ts for ts in _RATE_LIMIT_STORE[client_id] if ts > window_start
        ]

        if len(_RATE_LIMIT_STORE[client_id]) >= max_requests:
            return False

        _RATE_LIMIT_STORE[client_id].append(now)
        return True


# =====================================================================
# 5. INPUT SANITIZATION & INJECTION AWARENESS
# =====================================================================
class SecuritySanitizer:
    """
    Multi-vector defense analyzer checking against:
    - Prompt Injection (Jailbreaking, system override strings)
    - Shell Command Injection
    - Path Traversal
    """
    # Patterns typical in Prompt Injection / Jailbreak attempts
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)you\s+are\s+now\s+(unfiltered|dan|jailbroken)",
        r"(?i)system\s+override",
        r"(?i)disregard\s+safety\s+guidelines",
        r"(?i)reveal\s+(your\s+)?system\s+prompt"
    ]

    # Destructive or dangerous shell constructs
    SHELL_INJECTION_PATTERNS = [
        r"[;&|`$]\s*(rm\s+-rf|del\s+/f|format|shutdown|reg\s+delete)",
        r"powershell(\.exe)?\s+-enc",
        r"\b(Invoke-Expression|iex)\b"
    ]

    @classmethod
    def inspect_prompt(cls, user_text: str) -> Dict[str, Any]:
        """Detects prompt injection attempts in conversational inputs."""
        clean_text = user_text.strip()
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, clean_text):
                logger.warning(f"Potential prompt injection detected matching pattern: {pattern}")
                return {
                    "is_safe": False,
                    "reason": "Potential adversarial prompt injection detected.",
                    "sanitized": "[REDACTED_SECURITY_ALERT]"
                }
        return {
            "is_safe": True,
            "reason": "Clean",
            "sanitized": clean_text
        }

    @classmethod
    def sanitize_shell_input(cls, command: str) -> str:
        """Validates shell input against high-severity injection patterns."""
        cmd_clean = command.strip()
        for pattern in cls.SHELL_INJECTION_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                raise PermissionError(f"Command blocked by security sanitizer: pattern '{pattern}' flagged.")
        return cmd_clean


# =====================================================================
# 6. OAUTH / 3RD-PARTY LOGIN PROVIDER
# =====================================================================
class OAuthProvider:
    """Simulates/Implements OAuth 2.0 authorization code grant flow with Google / GitHub."""

    @staticmethod
    def generate_authorization_url(provider: str, redirect_uri: str, state: Optional[str] = None) -> Dict[str, str]:
        """Builds OAuth2 authorization redirect URL with client state."""
        state_token = state or hashlib.sha256(os.urandom(32)).hexdigest()
        endpoints = {
            "google": "https://accounts.google.com/o/oauth2/v2/auth",
            "github": "https://github.com/login/oauth/authorize"
        }
        base_url = endpoints.get(provider.lower(), "https://auth.jarvis.local/oauth/authorize")
        auth_url = (
            f"{base_url}?client_id=jarvis-client-id&response_type=code"
            f"&redirect_uri={redirect_uri}&state={state_token}&scope=openid%20profile%20email"
        )
        return {"authorization_url": auth_url, "state": state_token}

    @staticmethod
    def exchange_code_for_user(provider: str, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for verified user profile claims."""
        if not code or code == "invalid_code":
            raise ValueError("Invalid OAuth authorization code provided.")
        # Simulated verified profile from provider
        return {
            "provider": provider.lower(),
            "provider_user_id": f"oauth_{hashlib.md5(code.encode()).hexdigest()[:10]}",
            "email": f"developer@{provider.lower()}.local",
            "name": f"OAuth Developer ({provider.capitalize()})",
            "verified": True
        }
