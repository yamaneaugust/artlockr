"""
Security Management API Endpoints

Endpoints for:
- Organization blocking/unblocking
- IP reputation management
- Security analytics
- Verification token generation
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.models.database import Artist, Artwork, DetectionResult
from backend.app.services.security import (
    ip_reputation,
    rate_limiter,
    behavioral_detector,
    org_blocker,
    request_verifier
)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class BlockOrganizationRequest(BaseModel):
    organization_identifier: str
    reason: str
    detection_id: Optional[int] = None


class UnblockOrganizationRequest(BaseModel):
    organization_identifier: str


class IPReputationResponse(BaseModel):
    ip: str
    score: float
    category: str
    request_count: int
    failed_auth_count: int
    is_blocked: bool


class SecurityAnalyticsResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    suspicious_requests: int
    top_blocked_ips: List[dict]
    attack_patterns: List[str]


class VerificationTokenResponse(BaseModel):
    token: str
    expires_at: int
    usage: str


# ============================================================================
# Organization Blocking Endpoints
# ============================================================================

@router.post("/block-organization")
async def block_organization(
    request_data: BlockOrganizationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Block an organization from accessing your artwork.

    Use this after detecting copyright infringement to prevent the
    infringing organization from accessing your artwork through the API.

    Args:
        organization_identifier: Domain, API key hash, or company name
        reason: Reason for blocking (e.g., "copyright infringement")
        detection_id: Optional ID of the detection that found infringement

    Returns:
        Confirmation of blocking
    """
    # Get current artist (would need authentication)
    # For now, assume artist_id is in request state
    artist_id = getattr(request.state, 'artist_id', 1)

    # If detection_id provided, verify it belongs to this artist
    metadata = {}
    if request_data.detection_id:
        result = await db.execute(
            select(DetectionResult).where(
                DetectionResult.id == request_data.detection_id,
                DetectionResult.artist_id == artist_id
            )
        )
        detection = result.scalar_one_or_none()

        if detection:
            metadata = {
                'detection_id': request_data.detection_id,
                'matches_found': detection.matches_found,
                'scan_date': detection.scan_date.isoformat()
            }

    # Block the organization
    org_blocker.block_organization(
        artist_id=artist_id,
        org_identifier=request_data.organization_identifier,
        reason=request_data.reason,
        metadata=metadata
    )

    return {
        "success": True,
        "message": f"Organization '{request_data.organization_identifier}' has been blocked",
        "artist_id": artist_id,
        "organization": request_data.organization_identifier,
        "reason": request_data.reason,
        "blocked_at": datetime.utcnow().isoformat()
    }


@router.post("/unblock-organization")
async def unblock_organization(
    request_data: UnblockOrganizationRequest,
    request: Request
):
    """
    Unblock a previously blocked organization.

    Args:
        organization_identifier: Organization to unblock

    Returns:
        Confirmation of unblocking
    """
    artist_id = getattr(request.state, 'artist_id', 1)

    org_blocker.unblock_organization(
        artist_id=artist_id,
        org_identifier=request_data.organization_identifier
    )

    return {
        "success": True,
        "message": f"Organization '{request_data.organization_identifier}' has been unblocked",
        "artist_id": artist_id,
        "organization": request_data.organization_identifier
    }


@router.get("/blocked-organizations")
async def get_blocked_organizations(request: Request):
    """
    Get list of all organizations blocked by you.

    Returns:
        List of blocked organizations with metadata
    """
    artist_id = getattr(request.state, 'artist_id', 1)

    blocked_orgs = org_blocker.get_blocked_organizations(artist_id)

    return {
        "artist_id": artist_id,
        "total_blocked": len(blocked_orgs),
        "blocked_organizations": blocked_orgs
    }


# ============================================================================
# IP Reputation Endpoints
# ============================================================================

@router.get("/ip-reputation/{ip}")
async def get_ip_reputation(ip: str):
    """
    Get reputation information for an IP address.

    Args:
        ip: IP address to check

    Returns:
        Reputation score and metadata
    """
    score = ip_reputation.ip_scores.get(ip, 75.0)
    category = ip_reputation.get_reputation_category(score)

    request_history = ip_reputation.request_history.get(ip, [])
    failed_auth = ip_reputation.failed_auth.get(ip, 0)

    is_blocked = ip_reputation.is_blocked(ip)
    in_allowlist = ip in ip_reputation.allowlist
    in_blocklist = ip in ip_reputation.blocklist

    return {
        "ip": ip,
        "reputation_score": round(score, 2),
        "category": category,
        "request_count": len(request_history),
        "failed_auth_count": failed_auth,
        "is_blocked": is_blocked,
        "in_allowlist": in_allowlist,
        "in_blocklist": in_blocklist,
        "user_agents_count": len(ip_reputation.user_agents.get(ip, set()))
    }


@router.post("/ip-reputation/block/{ip}")
async def block_ip(ip: str, reason: str = "manual"):
    """
    Manually block an IP address.

    Args:
        ip: IP address to block
        reason: Reason for blocking

    Returns:
        Confirmation
    """
    ip_reputation.add_to_blocklist(ip, reason)

    return {
        "success": True,
        "message": f"IP {ip} has been blocked",
        "ip": ip,
        "reason": reason
    }


@router.post("/ip-reputation/allow/{ip}")
async def allow_ip(ip: str):
    """
    Add IP to allowlist (trusted source).

    Args:
        ip: IP address to allow

    Returns:
        Confirmation
    """
    ip_reputation.add_to_allowlist(ip)

    return {
        "success": True,
        "message": f"IP {ip} has been added to allowlist",
        "ip": ip,
        "reputation_score": 100.0
    }


# ============================================================================
# Rate Limit Endpoints
# ============================================================================

@router.get("/rate-limit/status")
async def get_rate_limit_status(request: Request):
    """
    Get current rate limit status for your IP.

    Returns:
        Rate limit usage statistics
    """
    ip = request.client.host

    # Get stats for different limit types
    ip_stats = rate_limiter.get_usage_stats(ip, limit_type='ip')

    return {
        "ip": ip,
        "ip_rate_limit": ip_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/rate-limit/config")
async def get_rate_limit_config():
    """
    Get current rate limit configuration.

    Returns:
        Rate limit settings for different limit types
    """
    return {
        "rate_limits": rate_limiter.limits,
        "description": {
            "ip": "Rate limit per IP address",
            "user": "Rate limit per authenticated user",
            "api_key": "Rate limit per API key"
        }
    }


# ============================================================================
# Security Analytics Endpoints
# ============================================================================

@router.get("/security/analytics")
async def get_security_analytics():
    """
    Get security analytics and attack statistics.

    Returns:
        Security metrics and detected attack patterns
    """
    # Aggregate data from security services
    total_ips = len(ip_reputation.ip_scores)
    blocked_ips = sum(1 for ip, score in ip_reputation.ip_scores.items() if score < 25)
    suspicious_ips = sum(1 for ip, score in ip_reputation.ip_scores.items() if 25 <= score < 50)

    # Get top blocked IPs
    top_blocked = sorted(
        [(ip, score) for ip, score in ip_reputation.ip_scores.items() if score < 50],
        key=lambda x: x[1]
    )[:10]

    top_blocked_list = [
        {
            "ip": ip,
            "reputation_score": round(score, 2),
            "category": ip_reputation.get_reputation_category(score)
        }
        for ip, score in top_blocked
    ]

    # Get attack patterns
    attack_patterns = []
    for ip, patterns in behavioral_detector.access_patterns.items():
        if len(patterns['endpoints']) > 20:
            attack_patterns.append(f"Endpoint scanning from {ip}")

    return {
        "total_tracked_ips": total_ips,
        "blocked_ips": blocked_ips,
        "suspicious_ips": suspicious_ips,
        "trusted_ips": len(ip_reputation.allowlist),
        "top_blocked_ips": top_blocked_list,
        "detected_attack_patterns": attack_patterns,
        "total_organizations_blocked": sum(len(orgs) for orgs in org_blocker.blocked_orgs.values()),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/security/behavioral-analysis/{ip}")
async def get_behavioral_analysis(ip: str):
    """
    Get detailed behavioral analysis for an IP.

    Args:
        ip: IP address to analyze

    Returns:
        Behavioral patterns and anomaly scores
    """
    patterns = behavioral_detector.access_patterns.get(ip)

    if not patterns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for IP {ip}"
        )

    return {
        "ip": ip,
        "endpoints_accessed": dict(patterns['endpoints']),
        "total_requests": len(patterns['timestamps']),
        "unique_endpoints": len(patterns['endpoints']),
        "header_fingerprints": len(patterns['header_fingerprints']),
        "analysis": "Use POST /api/detect endpoint to trigger real-time analysis"
    }


# ============================================================================
# Verification Token Endpoints
# ============================================================================

@router.post("/security/generate-token")
async def generate_verification_token(request: Request):
    """
    Generate a verification token for enhanced security.

    Use this token in the `X-Verification-Token` header for requests
    that require additional verification.

    Returns:
        Verification token and usage instructions
    """
    ip = request.client.host

    token = request_verifier.generate_challenge_token(ip)

    return {
        "token": token,
        "expires_at": int(datetime.utcnow().timestamp()) + 300,  # 5 minutes
        "usage": "Include this token in the 'X-Verification-Token' header",
        "example": {
            "headers": {
                "X-Verification-Token": token
            }
        }
    }


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/security/health")
async def security_health_check():
    """
    Check health of security services.

    Returns:
        Status of all security components
    """
    return {
        "status": "healthy",
        "services": {
            "ip_reputation": "active",
            "rate_limiter": "active",
            "behavioral_detector": "active",
            "organization_blocker": "active",
            "request_verifier": "active"
        },
        "statistics": {
            "tracked_ips": len(ip_reputation.ip_scores),
            "blocked_ips": len(ip_reputation.blocklist),
            "allowed_ips": len(ip_reputation.allowlist),
            "active_rate_limits": len(rate_limiter.request_logs)
        },
        "timestamp": datetime.utcnow().isoformat()
    }
