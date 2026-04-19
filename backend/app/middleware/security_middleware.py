"""
Security Middleware for API Protection

Applies comprehensive security measures:
- IP reputation checking
- Rate limiting
- Behavioral analysis
- Request verification
- Attack detection

Usage:
    app.add_middleware(SecurityMiddleware)
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from typing import Callable

from app.services.security import (
    ip_reputation,
    rate_limiter,
    behavioral_detector,
    request_verifier
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware.

    Applies multiple layers of security:
    1. IP reputation checking
    2. Rate limiting (per IP)
    3. Behavioral analysis
    4. Request verification
    5. Attack pattern detection
    """

    def __init__(self, app, enable_strict_mode: bool = False):
        super().__init__(app)
        self.enable_strict_mode = enable_strict_mode

        # Endpoints to exclude from strict security (public endpoints)
        self.public_endpoints = {
            '/',
            '/docs',
            '/openapi.json',
            '/health',
            '/api/art-styles'
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security layers."""

        # Skip security for public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)

        # Get client IP
        ip = self._get_client_ip(request)

        # --- Layer 1: IP Reputation ---
        reputation_score = ip_reputation.calculate_reputation_score(ip, request)
        reputation_category = ip_reputation.get_reputation_category(reputation_score)

        # Block malicious IPs immediately
        if ip_reputation.is_blocked(ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Access denied",
                    "reason": "IP blocked due to malicious activity",
                    "reputation_score": reputation_score,
                    "category": reputation_category
                }
            )

        # --- Layer 2: Rate Limiting ---
        is_limited, retry_after = rate_limiter.is_rate_limited(ip, limit_type='ip')

        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "message": f"Too many requests. Please try again in {retry_after} seconds."
                },
                headers={"Retry-After": str(retry_after)}
            )

        # --- Layer 3: Behavioral Analysis ---
        behavior_analysis = behavioral_detector.analyze_request(ip, request)

        # In strict mode, block high-risk requests
        if self.enable_strict_mode and behavior_analysis['is_suspicious']:
            if behavior_analysis['recommendation'] == 'block':
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Suspicious activity detected",
                        "risk_score": behavior_analysis['risk_score'],
                        "patterns": behavior_analysis['anomalies']
                    }
                )

        # --- Layer 4: Request Verification ---
        is_verified, verification_reason = request_verifier.verify_request(request, ip)

        # Warn on unverified requests (but allow in non-strict mode)
        if not is_verified and self.enable_strict_mode:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Request verification failed",
                    "reason": verification_reason,
                    "message": "Please use a verified client or browser"
                }
            )

        # --- Process Request ---
        start_time = time.time()

        # Add security metadata to request state
        request.state.security = {
            'ip': ip,
            'reputation_score': reputation_score,
            'reputation_category': reputation_category,
            'behavior_analysis': behavior_analysis,
            'is_verified': is_verified
        }

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add security headers to response
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Add rate limit info to headers
        usage_stats = rate_limiter.get_usage_stats(ip, limit_type='ip')
        response.headers['X-RateLimit-Limit'] = str(usage_stats.get('limit', 100))
        response.headers['X-RateLimit-Remaining'] = str(usage_stats.get('remaining', 100))
        response.headers['X-RateLimit-Reset'] = str(usage_stats.get('reset_at', 0))

        # Add reputation score (for debugging/monitoring)
        if request.url.path.startswith('/api/'):
            response.headers['X-Reputation-Score'] = str(int(reputation_score))

        # Process time
        process_time = time.time() - start_time
        response.headers['X-Process-Time'] = f"{process_time:.3f}"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request (handles proxies)."""
        # Check X-Forwarded-For header (from proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take first IP (client IP)
            return forwarded_for.split(',')[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        # Fall back to direct client
        return request.client.host


class OrganizationBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce organization blocking.

    Checks if requesting organization is blocked by the artist
    whose artwork is being accessed.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check organization blocking before processing request."""

        # Only apply to artwork access endpoints
        if not request.url.path.startswith('/api/artwork/'):
            return await call_next(request)

        # Get organization identifier from request
        org_id = self._extract_organization_id(request)

        if not org_id:
            # No organization identifier - allow (regular user)
            return await call_next(request)

        # Extract artwork_id from path
        # Example: /api/artwork/123/... -> 123
        import re
        match = re.search(r'/api/artwork/(\d+)', request.url.path)
        if not match:
            return await call_next(request)

        artwork_id = int(match.group(1))

        # Get artist_id for this artwork (would need database access)
        # For now, store in request state for endpoint to check
        request.state.organization_id = org_id
        request.state.needs_blocking_check = True

        return await call_next(request)

    def _extract_organization_id(self, request: Request) -> str:
        """
        Extract organization identifier from request.

        Can be extracted from:
        - API key
        - Domain (from Referer header)
        - Custom header (X-Organization-ID)
        """
        # Check custom header
        org_header = request.headers.get('X-Organization-ID')
        if org_header:
            return org_header

        # Extract from API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Hash the API key to use as identifier
            import hashlib
            return hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # Extract from Referer domain
        referer = request.headers.get('Referer')
        if referer:
            import urllib.parse
            parsed = urllib.parse.urlparse(referer)
            return parsed.netloc

        return None


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting with tiered limits.

    Different endpoints have different rate limits:
    - Upload endpoints: Stricter limits
    - Detection endpoints: Moderate limits
    - Public endpoints: Lenient limits
    """

    def __init__(self, app):
        super().__init__(app)

        # Endpoint-specific rate limits (requests per minute)
        self.endpoint_limits = {
            '/api/upload': 10,
            '/api/detect': 30,
            '/api/privacy': 20,
            'default': 100
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply endpoint-specific rate limiting."""

        # Get client IP
        ip = self._get_client_ip(request)

        # Determine rate limit for this endpoint
        limit = self._get_endpoint_limit(request.url.path)

        # Create unique identifier for this IP + endpoint combo
        identifier = f"{ip}:{request.url.path}"

        # Temporarily update rate limit for this check
        original_limit = rate_limiter.limits['ip'].copy()
        rate_limiter.update_limits('ip', requests=limit, window=60)

        is_limited, retry_after = rate_limiter.is_rate_limited(
            identifier, limit_type='ip'
        )

        # Restore original limit
        rate_limiter.limits['ip'] = original_limit

        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded for this endpoint",
                    "endpoint": request.url.path,
                    "limit": f"{limit} requests per minute",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        return request.client.host

    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit for endpoint path."""
        for endpoint_prefix, limit in self.endpoint_limits.items():
            if endpoint_prefix in path:
                return limit

        return self.endpoint_limits['default']
