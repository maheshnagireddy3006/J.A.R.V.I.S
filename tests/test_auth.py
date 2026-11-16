"""
UNIT TESTS: AUTHENTICATION, PASSWORD HASHING, JWT, RBAC & RATE LIMITING
"""

import pytest
from auth import PasswordSecurity, TokenManager, RBAC, RateLimiter, SecuritySanitizer


def test_password_hashing_and_verification():
    raw_pwd = "StarkIndustries2026!"
    hashed = PasswordSecurity.hash_password(raw_pwd)

    assert "$" in hashed
    assert PasswordSecurity.verify_password(raw_pwd, hashed) is True
    assert PasswordSecurity.verify_password("WrongPassword!", hashed) is False


def test_jwt_issuance_and_decode():
    username = "tony_stark"
    role = "admin"
    token = TokenManager.create_access_token(subject=username, role=role)

    assert isinstance(token, str)
    claims = TokenManager.decode_token(token)
    assert claims["sub"] == username
    assert claims["role"] == role
    assert "exp" in claims


def test_jwt_invalid_token():
    with pytest.raises(PermissionError):
        TokenManager.decode_token("invalid.jwt.token")


def test_rbac_authorization_hierarchy():
    # Admin possesses all privileges
    assert RBAC.is_authorized("admin", "admin") is True
    assert RBAC.is_authorized("admin", "operator") is True
    assert RBAC.is_authorized("admin", "guest") is True

    # Operator cannot perform admin tasks
    assert RBAC.is_authorized("operator", "admin") is False
    assert RBAC.is_authorized("operator", "operator") is True

    # Guest can only perform guest tasks
    assert RBAC.is_authorized("guest", "operator") is False


def test_rate_limiter_window():
    client_ip = "192.168.1.100"
    # First 3 requests allowed under threshold of 3
    assert RateLimiter.is_allowed(client_ip, max_requests=3, window_seconds=10) is True
    assert RateLimiter.is_allowed(client_ip, max_requests=3, window_seconds=10) is True
    assert RateLimiter.is_allowed(client_ip, max_requests=3, window_seconds=10) is True
    # 4th request must be rejected
    assert RateLimiter.is_allowed(client_ip, max_requests=3, window_seconds=10) is False
