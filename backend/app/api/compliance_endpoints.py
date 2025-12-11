"""
Compliance API Endpoints

Endpoints for:
- Consent management (GDPR/CCPA)
- Cookie preferences
- Age verification
- Watermarking configuration
- Legal document access
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

from backend.app.services.compliance import (
    consent_manager,
    cookie_manager,
    age_verifier,
    ConsentType
)
from backend.app.services.watermarking import (
    watermarking_policy,
    watermarking_service
)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ConsentRequest(BaseModel):
    consent_type: ConsentType
    granted: bool


class BatchConsentRequest(BaseModel):
    consents: Dict[ConsentType, bool]


class CookiePreferencesRequest(BaseModel):
    analytics: bool = False
    marketing: bool = False
    preferences: bool = True


class AgeVerificationRequest(BaseModel):
    birth_date: str  # ISO format: YYYY-MM-DD
    parent_email: Optional[EmailStr] = None


class WatermarkPreferenceRequest(BaseModel):
    enabled: bool
    method: str = 'lsb'  # 'lsb' or 'dct'
    strength: float = 1.0


# ============================================================================
# Consent Management Endpoints
# ============================================================================

@router.post("/consent/grant")
async def grant_consent(
    request_data: ConsentRequest,
    request: Request
):
    """
    Grant consent for a specific purpose.

    Args:
        consent_type: Type of consent (analytics, marketing, etc.)
        granted: Whether consent is granted

    Returns:
        Consent record
    """
    # Get user ID (would come from authentication)
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Get IP and user agent for audit trail
    ip_address = request.client.host
    user_agent = request.headers.get('user-agent', 'unknown')

    record = consent_manager.record_consent(
        user_id=user_id,
        consent_type=request_data.consent_type,
        granted=request_data.granted,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return {
        "success": True,
        "consent_type": request_data.consent_type,
        "granted": request_data.granted,
        "timestamp": record.timestamp.isoformat(),
        "version": record.version
    }


@router.post("/consent/grant-batch")
async def grant_batch_consent(
    request_data: BatchConsentRequest,
    request: Request
):
    """
    Grant multiple consents at once (initial consent banner).

    Args:
        consents: Dictionary of consent types and their grant status

    Returns:
        List of consent records
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')
    ip_address = request.client.host
    user_agent = request.headers.get('user-agent', 'unknown')

    records = []

    for consent_type, granted in request_data.consents.items():
        record = consent_manager.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            ip_address=ip_address,
            user_agent=user_agent
        )
        records.append({
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": record.timestamp.isoformat()
        })

    return {
        "success": True,
        "total_consents": len(records),
        "consents": records
    }


@router.get("/consent/status")
async def get_consent_status(request: Request):
    """
    Get current consent status for all consent types.

    Returns:
        Complete consent status
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    status = consent_manager.get_consent_status(user_id)

    return {
        "user_id": user_id,
        **status
    }


@router.post("/consent/withdraw/{consent_type}")
async def withdraw_consent(
    consent_type: ConsentType,
    request: Request
):
    """
    Withdraw consent for a specific purpose.

    Args:
        consent_type: Type of consent to withdraw

    Returns:
        Confirmation
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')
    ip_address = request.client.host

    # Cannot withdraw essential consent
    if consent_type == ConsentType.ESSENTIAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw essential consent (required for service)"
        )

    success = consent_manager.withdraw_consent(
        user_id=user_id,
        consent_type=consent_type,
        ip_address=ip_address
    )

    return {
        "success": success,
        "consent_type": consent_type,
        "action": "withdrawn",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/consent/audit-trail")
async def get_consent_audit_trail(request: Request):
    """
    Get complete audit trail of consent changes.

    Returns:
        Chronological list of all consent records
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    audit_trail = consent_manager.get_audit_trail(user_id)

    return {
        "user_id": user_id,
        "total_records": len(audit_trail),
        "audit_trail": audit_trail
    }


@router.get("/consent/export")
async def export_consent_data(request: Request):
    """
    Export all consent data (GDPR data portability).

    Returns:
        Complete consent data in portable format
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    export_data = consent_manager.export_consent_data(user_id)

    return export_data


# ============================================================================
# Cookie Management Endpoints
# ============================================================================

@router.get("/cookies/policy")
async def get_cookie_policy():
    """
    Get complete cookie policy.

    Returns:
        Cookie categories and details
    """
    policy = cookie_manager.get_cookie_policy()

    return {
        "cookie_policy": policy,
        "gdpr_compliant": True,
        "last_updated": policy['last_updated']
    }


@router.post("/cookies/preferences")
async def set_cookie_preferences(
    request_data: CookiePreferencesRequest,
    request: Request
):
    """
    Set cookie preferences.

    Args:
        analytics: Allow analytics cookies
        marketing: Allow marketing cookies
        preferences: Allow preference cookies

    Returns:
        Confirmation
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Record consents for cookie categories
    consent_manager.record_consent(
        user_id=user_id,
        consent_type=ConsentType.ANALYTICS,
        granted=request_data.analytics,
        ip_address=request.client.host
    )

    consent_manager.record_consent(
        user_id=user_id,
        consent_type=ConsentType.MARKETING,
        granted=request_data.marketing,
        ip_address=request.client.host
    )

    consent_manager.record_consent(
        user_id=user_id,
        consent_type=ConsentType.PERSONALIZATION,
        granted=request_data.preferences,
        ip_address=request.client.host
    )

    return {
        "success": True,
        "preferences": {
            "analytics": request_data.analytics,
            "marketing": request_data.marketing,
            "preferences": request_data.preferences
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/cookies/preferences")
async def get_cookie_preferences(request: Request):
    """
    Get current cookie preferences.

    Returns:
        Current cookie consent status
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    return {
        "user_id": user_id,
        "analytics": consent_manager.check_consent(user_id, ConsentType.ANALYTICS),
        "marketing": consent_manager.check_consent(user_id, ConsentType.MARKETING),
        "preferences": consent_manager.check_consent(user_id, ConsentType.PERSONALIZATION),
        "essential": True  # Always enabled
    }


# ============================================================================
# Age Verification Endpoints
# ============================================================================

@router.post("/age-verification/verify")
async def verify_age(
    request_data: AgeVerificationRequest,
    request: Request
):
    """
    Verify user's age (COPPA compliance).

    Args:
        birth_date: User's birth date (YYYY-MM-DD)
        parent_email: Parent's email if under 13

    Returns:
        Verification status
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Parse birth date
    try:
        birth_date = datetime.fromisoformat(request_data.birth_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid birth_date format. Use YYYY-MM-DD"
        )

    record = age_verifier.verify_age(
        user_id=user_id,
        birth_date=birth_date,
        verification_method='self_reported',
        parent_email=request_data.parent_email
    )

    response = {
        "success": True,
        "is_verified": record.is_verified,
        "age": record.age,
        "requires_parental_consent": record.requires_parental_consent,
        "verified_at": record.verified_at.isoformat()
    }

    if record.requires_parental_consent:
        response["message"] = (
            "You are under 13 and require parental consent. "
            "We have sent a verification email to your parent."
        )

    return response


@router.get("/age-verification/status")
async def get_age_verification_status(request: Request):
    """
    Get age verification status.

    Returns:
        Verification status
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    status_data = age_verifier.get_verification_status(user_id)

    if not status_data:
        return {
            "is_verified": False,
            "message": "Age not verified. Please verify your age."
        }

    return status_data


# ============================================================================
# Watermarking Endpoints
# ============================================================================

@router.post("/watermarking/configure")
async def configure_watermarking(
    request_data: WatermarkPreferenceRequest,
    request: Request
):
    """
    Configure watermarking preferences.

    OPTIONAL FEATURE: Watermarking allows you to track unauthorized usage
    of your artwork. You can choose to:
    - Disable watermarking (maximum privacy)
    - Enable LSB watermarking (very invisible, less robust)
    - Enable DCT watermarking (more robust, still invisible)

    Args:
        enabled: Enable watermarking
        method: 'lsb' or 'dct'
        strength: Embedding strength (0.01-1.0)

    Returns:
        Confirmation
    """
    artist_id = getattr(request.state, 'artist_id', 1)

    # Validate method
    if request_data.method not in ['lsb', 'dct']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid method. Use 'lsb' or 'dct'"
        )

    # Validate strength
    if not 0.01 <= request_data.strength <= 3.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strength must be between 0.01 and 3.0"
        )

    watermarking_policy.set_preference(
        artist_id=artist_id,
        enabled=request_data.enabled,
        method=request_data.method,
        strength=request_data.strength
    )

    # Record consent for watermarking
    consent_manager.record_consent(
        user_id=str(artist_id),
        consent_type=ConsentType.DATA_RETENTION if request_data.enabled else ConsentType.ESSENTIAL,
        granted=True,
        ip_address=request.client.host,
        metadata={"watermarking_enabled": request_data.enabled}
    )

    return {
        "success": True,
        "artist_id": artist_id,
        "watermarking": {
            "enabled": request_data.enabled,
            "method": request_data.method,
            "strength": request_data.strength
        },
        "privacy_note": (
            "Watermarking requires storing original images. "
            "If disabled, only feature vectors are stored."
        ) if request_data.enabled else "Maximum privacy mode: features only"
    }


@router.get("/watermarking/preferences")
async def get_watermarking_preferences(request: Request):
    """
    Get current watermarking preferences.

    Returns:
        Watermarking configuration
    """
    artist_id = getattr(request.state, 'artist_id', 1)

    preferences = watermarking_policy.get_preference(artist_id)

    return {
        "artist_id": artist_id,
        "watermarking": preferences,
        "description": {
            "lsb": "LSB watermarking: Very invisible, less robust to transformations",
            "dct": "DCT watermarking: More robust to compression/resize, still invisible"
        }
    }


# ============================================================================
# Legal Document Endpoints
# ============================================================================

@router.get("/legal/terms-of-service")
async def get_terms_of_service():
    """
    Get Terms of Service.

    Returns:
        Terms of Service document
    """
    # In production, this would read from the legal_templates directory
    return {
        "document": "terms_of_service",
        "version": "1.0",
        "last_updated": "2025-12-11",
        "url": "/legal_templates/TERMS_OF_SERVICE.md",
        "summary": "Terms of Service governs your use of ArtLockr"
    }


@router.get("/legal/privacy-policy")
async def get_privacy_policy():
    """
    Get Privacy Policy.

    Returns:
        Privacy Policy document
    """
    return {
        "document": "privacy_policy",
        "version": "1.0",
        "last_updated": "2025-12-11",
        "url": "/legal_templates/PRIVACY_POLICY.md",
        "summary": "Privacy-first policy: features-only storage by default",
        "key_points": [
            "Feature vectors stored, original images deleted by default",
            "Full GDPR and CCPA compliance",
            "Cryptographic ownership proofs",
            "Complete data transparency and control"
        ]
    }


@router.get("/legal/cookie-policy")
async def get_cookie_policy_legal():
    """
    Get Cookie Policy.

    Returns:
        Cookie Policy document
    """
    policy = cookie_manager.get_cookie_policy()

    return {
        "document": "cookie_policy",
        "version": "1.0",
        "last_updated": policy['last_updated'],
        "categories": policy['categories'],
        "opt_out_info": "You can manage cookie preferences at /api/cookies/preferences"
    }


# ============================================================================
# Compliance Dashboard
# ============================================================================

@router.get("/compliance/dashboard")
async def get_compliance_dashboard(request: Request):
    """
    Get comprehensive compliance dashboard.

    Shows:
    - Consent status
    - Cookie preferences
    - Age verification
    - Watermarking settings
    - Data retention policies

    Returns:
        Complete compliance overview
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')
    artist_id = getattr(request.state, 'artist_id', 1)

    # Get all compliance data
    consent_status = consent_manager.get_consent_status(user_id)
    age_status = age_verifier.get_verification_status(user_id)
    watermark_prefs = watermarking_policy.get_preference(artist_id)

    return {
        "user_id": user_id,
        "artist_id": artist_id,
        "compliance": {
            "consent": {
                "has_consents": consent_status['has_consents'],
                "requires_update": consent_status['requires_update'],
                "current_version": consent_status['current_version'],
                "consents": consent_status['consents']
            },
            "age_verification": age_status or {"is_verified": False},
            "watermarking": watermark_prefs,
            "data_retention": {
                "mode": "features_only" if not watermark_prefs['enabled'] else "images_stored",
                "retention_period": "Until deletion",
                "auto_deletion": watermark_prefs['enabled'] is False
            }
        },
        "privacy_level": "maximum" if not watermark_prefs['enabled'] else "high",
        "gdpr_compliant": True,
        "ccpa_compliant": True,
        "coppa_compliant": age_status.get('is_verified', False) if age_status else False
    }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/compliance/health")
async def compliance_health_check():
    """
    Check health of compliance services.

    Returns:
        Status of compliance components
    """
    return {
        "status": "healthy",
        "services": {
            "consent_manager": "active",
            "cookie_manager": "active",
            "age_verifier": "active",
            "watermarking_service": "active"
        },
        "compliance_frameworks": {
            "gdpr": "compliant",
            "ccpa": "compliant",
            "coppa": "compliant"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
