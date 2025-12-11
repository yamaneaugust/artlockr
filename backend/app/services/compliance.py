"""
Consent Management System for GDPR/CCPA Compliance

Manages user consent for:
- Data collection and processing
- Cookie usage
- Marketing communications
- Third-party data sharing
- Age verification

Provides:
- Granular consent options
- Consent withdrawal
- Audit trail
- Cookie banner configuration
- Age gate implementation
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import json


class ConsentType(str, Enum):
    """Types of consent that can be requested."""
    ESSENTIAL = "essential"  # Required for service (no opt-out)
    ANALYTICS = "analytics"  # Usage analytics and statistics
    MARKETING = "marketing"  # Marketing communications
    THIRD_PARTY = "third_party"  # Third-party data sharing
    PERSONALIZATION = "personalization"  # Personalized content
    COOKIES = "cookies"  # Non-essential cookies
    DATA_RETENTION = "data_retention"  # Long-term data retention
    AI_TRAINING = "ai_training"  # Use artwork for AI model training


class ConsentManager:
    """
    Manages user consent preferences and compliance.

    Features:
    - Granular consent management
    - Consent versioning (track changes to terms)
    - Automatic expiration (re-consent after 12 months)
    - Audit trail
    - GDPR/CCPA compliant
    """

    def __init__(self):
        # Store consent records: {user_id: {consent_type: ConsentRecord}}
        self.consent_records: Dict[str, Dict[str, 'ConsentRecord']] = {}

        # Consent version tracking
        self.current_consent_version = "1.0"
        self.consent_version_history = {
            "1.0": {
                "date": "2025-12-11",
                "changes": "Initial consent framework"
            }
        }

        # Consent expiration (12 months for GDPR)
        self.consent_expiry_days = 365

    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        ip_address: str = None,
        user_agent: str = None,
        metadata: Optional[Dict] = None
    ) -> 'ConsentRecord':
        """
        Record a consent decision.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent was granted
            ip_address: IP address of requester (for audit)
            user_agent: User agent (for audit)
            metadata: Additional metadata

        Returns:
            ConsentRecord object
        """
        if user_id not in self.consent_records:
            self.consent_records[user_id] = {}

        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            version=self.current_consent_version,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )

        self.consent_records[user_id][consent_type] = record

        return record

    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        require_current_version: bool = True
    ) -> bool:
        """
        Check if user has granted consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent to check
            require_current_version: Require consent on current version

        Returns:
            True if consent granted, False otherwise
        """
        # Essential consent is always granted (required for service)
        if consent_type == ConsentType.ESSENTIAL:
            return True

        if user_id not in self.consent_records:
            return False

        record = self.consent_records[user_id].get(consent_type)

        if not record:
            return False

        # Check if granted
        if not record.granted:
            return False

        # Check if expired
        if record.is_expired(self.consent_expiry_days):
            return False

        # Check version if required
        if require_current_version and record.version != self.current_consent_version:
            return False

        return True

    def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: str = None
    ) -> bool:
        """
        Withdraw consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent to withdraw
            ip_address: IP address (for audit)

        Returns:
            True if successful
        """
        # Cannot withdraw essential consent
        if consent_type == ConsentType.ESSENTIAL:
            return False

        # Record withdrawal as new consent record with granted=False
        self.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False,
            ip_address=ip_address,
            metadata={"action": "withdrawal"}
        )

        return True

    def get_consent_status(self, user_id: str) -> Dict[str, any]:
        """
        Get complete consent status for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with consent status for all types
        """
        if user_id not in self.consent_records:
            return {
                "has_consents": False,
                "consents": {},
                "requires_update": False
            }

        consents = {}
        requires_update = False

        for consent_type in ConsentType:
            record = self.consent_records[user_id].get(consent_type)

            if record:
                is_valid = not record.is_expired(self.consent_expiry_days)
                is_current_version = record.version == self.current_consent_version

                consents[consent_type] = {
                    "granted": record.granted,
                    "timestamp": record.timestamp.isoformat(),
                    "version": record.version,
                    "is_valid": is_valid,
                    "is_current_version": is_current_version,
                    "expires_at": record.get_expiry_date(self.consent_expiry_days).isoformat()
                }

                if not is_current_version or not is_valid:
                    requires_update = True
            else:
                consents[consent_type] = None

        return {
            "has_consents": True,
            "consents": consents,
            "requires_update": requires_update,
            "current_version": self.current_consent_version
        }

    def get_audit_trail(self, user_id: str) -> List[Dict]:
        """
        Get complete audit trail of consent changes.

        Args:
            user_id: User identifier

        Returns:
            List of all consent records (chronological)
        """
        # In production, this would query a database with full history
        # For now, return current state
        if user_id not in self.consent_records:
            return []

        audit_trail = []
        for consent_type, record in self.consent_records[user_id].items():
            audit_trail.append({
                "consent_type": consent_type,
                "granted": record.granted,
                "version": record.version,
                "timestamp": record.timestamp.isoformat(),
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "metadata": record.metadata
            })

        # Sort by timestamp
        audit_trail.sort(key=lambda x: x['timestamp'], reverse=True)

        return audit_trail

    def export_consent_data(self, user_id: str) -> Dict:
        """
        Export all consent data for a user (GDPR right to data portability).

        Args:
            user_id: User identifier

        Returns:
            Complete consent data in portable format
        """
        return {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "consent_status": self.get_consent_status(user_id),
            "audit_trail": self.get_audit_trail(user_id),
            "data_format_version": "1.0"
        }

    def delete_consent_data(self, user_id: str) -> bool:
        """
        Delete all consent data for a user (GDPR right to erasure).

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        if user_id in self.consent_records:
            del self.consent_records[user_id]
            return True
        return False


class ConsentRecord:
    """Individual consent record."""

    def __init__(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        version: str,
        timestamp: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.user_id = user_id
        self.consent_type = consent_type
        self.granted = granted
        self.version = version
        self.timestamp = timestamp
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}

    def is_expired(self, expiry_days: int) -> bool:
        """Check if consent has expired."""
        expiry_date = self.timestamp + timedelta(days=expiry_days)
        return datetime.utcnow() > expiry_date

    def get_expiry_date(self, expiry_days: int) -> datetime:
        """Get expiry date."""
        return self.timestamp + timedelta(days=expiry_days)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "consent_type": self.consent_type,
            "granted": self.granted,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata
        }


class CookieManager:
    """
    Manages cookie consent and classification.

    Cookie categories:
    - Essential: Required for service (no opt-out)
    - Analytics: Usage tracking
    - Marketing: Marketing and advertising
    - Preferences: User preferences
    """

    def __init__(self):
        # Cookie registry
        self.cookies = {
            "essential": [
                {
                    "name": "session_id",
                    "purpose": "User session management",
                    "duration": "Session",
                    "type": "Essential"
                },
                {
                    "name": "csrf_token",
                    "purpose": "Security protection against CSRF attacks",
                    "duration": "Session",
                    "type": "Essential"
                }
            ],
            "analytics": [
                {
                    "name": "analytics_id",
                    "purpose": "Anonymous usage analytics",
                    "duration": "1 year",
                    "type": "Analytics"
                }
            ],
            "marketing": [],
            "preferences": [
                {
                    "name": "theme_preference",
                    "purpose": "Remember UI theme preference",
                    "duration": "1 year",
                    "type": "Preferences"
                }
            ]
        }

    def get_cookie_policy(self) -> Dict:
        """Get complete cookie policy."""
        return {
            "last_updated": "2025-12-11",
            "categories": {
                "essential": {
                    "description": "Essential cookies are required for the service to function",
                    "opt_out": False,
                    "cookies": self.cookies["essential"]
                },
                "analytics": {
                    "description": "Analytics cookies help us understand how you use our service",
                    "opt_out": True,
                    "cookies": self.cookies["analytics"]
                },
                "marketing": {
                    "description": "Marketing cookies are used for advertising",
                    "opt_out": True,
                    "cookies": self.cookies["marketing"]
                },
                "preferences": {
                    "description": "Preference cookies remember your settings",
                    "opt_out": True,
                    "cookies": self.cookies["preferences"]
                }
            }
        }


class AgeVerification:
    """
    Age verification system for COPPA compliance.

    COPPA requires parental consent for users under 13.
    Some regions have higher age limits (16 in EU).
    """

    def __init__(self, minimum_age: int = 13):
        self.minimum_age = minimum_age

        # Track verified ages: {user_id: VerificationRecord}
        self.verifications: Dict[str, 'AgeVerificationRecord'] = {}

    def verify_age(
        self,
        user_id: str,
        birth_date: datetime,
        verification_method: str = "self_reported",
        parent_email: Optional[str] = None
    ) -> 'AgeVerificationRecord':
        """
        Verify user's age.

        Args:
            user_id: User identifier
            birth_date: User's birth date
            verification_method: How age was verified
            parent_email: Parent's email if under minimum_age

        Returns:
            AgeVerificationRecord
        """
        age = self._calculate_age(birth_date)
        is_verified = age >= self.minimum_age

        # For users under minimum age, require parental consent
        requires_parental_consent = age < self.minimum_age

        record = AgeVerificationRecord(
            user_id=user_id,
            birth_date=birth_date,
            age=age,
            is_verified=is_verified,
            verification_method=verification_method,
            requires_parental_consent=requires_parental_consent,
            parent_email=parent_email,
            verified_at=datetime.utcnow()
        )

        self.verifications[user_id] = record

        return record

    def is_verified(self, user_id: str) -> bool:
        """Check if user is age verified."""
        if user_id not in self.verifications:
            return False

        record = self.verifications[user_id]
        return record.is_verified or record.has_parental_consent

    def _calculate_age(self, birth_date: datetime) -> int:
        """Calculate age from birth date."""
        today = datetime.utcnow()
        age = today.year - birth_date.year

        # Adjust if birthday hasn't occurred this year
        if today.month < birth_date.month or (
            today.month == birth_date.month and today.day < birth_date.day
        ):
            age -= 1

        return age

    def get_verification_status(self, user_id: str) -> Optional[Dict]:
        """Get verification status for user."""
        if user_id not in self.verifications:
            return None

        record = self.verifications[user_id]

        return {
            "is_verified": record.is_verified,
            "age": record.age,
            "requires_parental_consent": record.requires_parental_consent,
            "has_parental_consent": record.has_parental_consent,
            "verified_at": record.verified_at.isoformat(),
            "verification_method": record.verification_method
        }


class AgeVerificationRecord:
    """Age verification record."""

    def __init__(
        self,
        user_id: str,
        birth_date: datetime,
        age: int,
        is_verified: bool,
        verification_method: str,
        requires_parental_consent: bool,
        parent_email: Optional[str],
        verified_at: datetime
    ):
        self.user_id = user_id
        self.birth_date = birth_date
        self.age = age
        self.is_verified = is_verified
        self.verification_method = verification_method
        self.requires_parental_consent = requires_parental_consent
        self.parent_email = parent_email
        self.verified_at = verified_at
        self.has_parental_consent = False  # Would be set separately

    def grant_parental_consent(self, parent_email: str):
        """Grant parental consent."""
        self.has_parental_consent = True
        self.parent_email = parent_email


# Global instances
consent_manager = ConsentManager()
cookie_manager = CookieManager()
age_verifier = AgeVerification(minimum_age=13)
