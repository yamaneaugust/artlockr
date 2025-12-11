# Compliance & Legal Framework

## Overview

ArtLockr is fully compliant with major privacy and data protection regulations:

✅ **GDPR** (General Data Protection Regulation) - European Union
✅ **CCPA** (California Consumer Privacy Act) - California, USA
✅ **COPPA** (Children's Online Privacy Protection Act) - USA

This document describes our compliance framework, consent management system, and legal policies.

---

## Table of Contents

1. [Compliance Framework](#compliance-framework)
2. [Consent Management](#consent-management)
3. [Cookie Management](#cookie-management)
4. [Age Verification](#age-verification)
5. [Watermarking (Optional)](#watermarking-optional)
6. [Privacy Rights](#privacy-rights)
7. [Legal Documents](#legal-documents)
8. [API Usage](#api-usage)

---

## Compliance Framework

### Multi-Regulation Compliance

| Regulation | Jurisdiction | Key Requirements | Our Compliance |
|------------|-------------|------------------|----------------|
| **GDPR** | EU/EEA | Consent, data minimization, right to erasure | ✅ Full compliance |
| **CCPA** | California | Right to know, delete, opt-out of sale | ✅ Full compliance |
| **COPPA** | USA | Parental consent for <13 | ✅ Full compliance |

### Privacy-First Architecture

**Default Mode: Maximum Privacy**

```
User uploads artwork
    ↓
Feature extraction (ResNet)
    ↓
Store 2048-dim vector
    ↓
DELETE original image  ← IMMEDIATE DELETION
    ↓
Generate cryptographic proof
    ↓
RESULT: Zero image storage, full functionality
```

**Privacy Levels:**

| Level | Image Storage | Features | Privacy | Compliance |
|-------|--------------|----------|---------|------------|
| **Maximum** | ❌ Deleted immediately | ✅ Stored | 100% | Default |
| **High** | ⏱️ Deleted after 24h | ✅ Stored | 95% | Multi-metric detection |
| **Moderate** | ✅ Stored | ✅ Stored | 80% | Full capabilities + watermarking |

---

## Consent Management

### Granular Consent System

ArtLockr implements **8 types of consent**:

| Consent Type | Required | Description | Can Withdraw |
|--------------|----------|-------------|--------------|
| **Essential** | ✅ Yes | Core service functionality | ❌ No |
| **Analytics** | ❌ No | Usage statistics and analytics | ✅ Yes |
| **Marketing** | ❌ No | Marketing communications | ✅ Yes |
| **Third Party** | ❌ No | Data sharing with third parties | ✅ Yes |
| **Personalization** | ❌ No | Personalized content | ✅ Yes |
| **Cookies** | ❌ No | Non-essential cookies | ✅ Yes |
| **Data Retention** | ❌ No | Long-term data storage | ✅ Yes |
| **AI Training** | ❌ No | Use artwork for AI model training | ✅ Yes |

### Consent Lifecycle

```
Initial Consent → Active (12 months) → Expired → Re-consent Required
                      ↓
                 Can Withdraw Anytime
                      ↓
                 Audit Trail Maintained
```

**Consent Features:**
- ✅ Versioning (track changes to terms)
- ✅ Automatic expiration (12 months, GDPR compliant)
- ✅ Audit trail (IP, timestamp, user agent)
- ✅ Easy withdrawal
- ✅ Export capabilities

### API Endpoints

**Grant Consent:**
```bash
POST /api/consent/grant

Body:
{
  "consent_type": "analytics",
  "granted": true
}

Response:
{
  "success": true,
  "consent_type": "analytics",
  "granted": true,
  "timestamp": "2025-12-11T10:00:00Z",
  "version": "1.0"
}
```

**Grant Multiple Consents (Initial Consent Banner):**
```bash
POST /api/consent/grant-batch

Body:
{
  "consents": {
    "analytics": true,
    "marketing": false,
    "personalization": true
  }
}

Response:
{
  "success": true,
  "total_consents": 3,
  "consents": [...]
}
```

**Check Consent Status:**
```bash
GET /api/consent/status

Response:
{
  "user_id": "user123",
  "has_consents": true,
  "requires_update": false,
  "current_version": "1.0",
  "consents": {
    "analytics": {
      "granted": true,
      "timestamp": "2025-12-11T10:00:00Z",
      "version": "1.0",
      "is_valid": true,
      "is_current_version": true,
      "expires_at": "2026-12-11T10:00:00Z"
    }
  }
}
```

**Withdraw Consent:**
```bash
POST /api/consent/withdraw/analytics

Response:
{
  "success": true,
  "consent_type": "analytics",
  "action": "withdrawn",
  "timestamp": "2025-12-11T11:00:00Z"
}
```

**Get Audit Trail:**
```bash
GET /api/consent/audit-trail

Response:
{
  "user_id": "user123",
  "total_records": 5,
  "audit_trail": [
    {
      "consent_type": "analytics",
      "granted": true,
      "version": "1.0",
      "timestamp": "2025-12-11T10:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "metadata": {}
    }
  ]
}
```

**Export Consent Data (GDPR Portability):**
```bash
GET /api/consent/export

Response:
{
  "user_id": "user123",
  "export_date": "2025-12-11T12:00:00Z",
  "consent_status": {...},
  "audit_trail": [...],
  "data_format_version": "1.0"
}
```

---

## Cookie Management

### Cookie Categories

**Essential Cookies** (cannot be disabled):
- `session_id`: User session management
- `csrf_token`: Security protection

**Analytics Cookies** (optional, requires consent):
- `analytics_id`: Anonymous usage analytics

**Preference Cookies** (optional):
- `theme_preference`: UI theme preference

### Cookie Policy

```bash
GET /api/cookies/policy

Response:
{
  "cookie_policy": {
    "last_updated": "2025-12-11",
    "categories": {
      "essential": {
        "description": "Essential cookies are required for the service to function",
        "opt_out": false,
        "cookies": [
          {
            "name": "session_id",
            "purpose": "User session management",
            "duration": "Session",
            "type": "Essential"
          }
        ]
      },
      "analytics": {
        "description": "Analytics cookies help us understand how you use our service",
        "opt_out": true,
        "cookies": [...]
      }
    }
  }
}
```

### Managing Cookie Preferences

**Set Preferences:**
```bash
POST /api/cookies/preferences

Body:
{
  "analytics": true,
  "marketing": false,
  "preferences": true
}

Response:
{
  "success": true,
  "preferences": {
    "analytics": true,
    "marketing": false,
    "preferences": true
  },
  "timestamp": "2025-12-11T10:00:00Z"
}
```

**Get Preferences:**
```bash
GET /api/cookies/preferences

Response:
{
  "user_id": "user123",
  "analytics": true,
  "marketing": false,
  "preferences": true,
  "essential": true
}
```

---

## Age Verification

### COPPA Compliance

**Age Requirements:**
- **13+**: Can create account with optional parental consent
- **Under 13**: Requires verified parental consent

**Verification Process:**

```
User provides birth date
    ↓
Calculate age
    ↓
If 13+: Verified ✅
If <13: Send parental consent email
    ↓
Parent verifies via email link
    ↓
Account activated
```

### API Endpoints

**Verify Age:**
```bash
POST /api/age-verification/verify

Body:
{
  "birth_date": "2010-05-15",  # YYYY-MM-DD
  "parent_email": "parent@example.com"  # Required if under 13
}

Response (13+):
{
  "success": true,
  "is_verified": true,
  "age": 15,
  "requires_parental_consent": false,
  "verified_at": "2025-12-11T10:00:00Z"
}

Response (<13):
{
  "success": true,
  "is_verified": false,
  "age": 12,
  "requires_parental_consent": true,
  "verified_at": "2025-12-11T10:00:00Z",
  "message": "You are under 13 and require parental consent. We have sent a verification email to your parent."
}
```

**Check Verification Status:**
```bash
GET /api/age-verification/status

Response:
{
  "is_verified": true,
  "age": 15,
  "requires_parental_consent": false,
  "has_parental_consent": false,
  "verified_at": "2025-12-11T10:00:00Z",
  "verification_method": "self_reported"
}
```

---

## Watermarking (Optional)

### Privacy vs. Tracking Trade-off

**Without Watermarking:**
- ✅ Maximum privacy (no images stored)
- ✅ Feature-only storage
- ❌ Cannot track unauthorized usage

**With Watermarking:**
- ⚠️ Original images must be stored
- ✅ Track artwork usage across internet
- ✅ Prove ownership of disputed artwork
- ✅ Forensic analysis of leaks

### Watermarking Methods

| Method | Invisibility | Robustness | Use Case |
|--------|-------------|------------|----------|
| **LSB** | Very high | Low | Simple tracking, no transformations |
| **DCT** | High | High | Robust to compression, resize |

### Watermark Payload

Format: `artist_id:artwork_id:timestamp:hash`

Example: `123:456:2025-12-11T10:00:00Z:a1b2c3d4`

### API Endpoints

**Configure Watermarking:**
```bash
POST /api/watermarking/configure

Body:
{
  "enabled": true,
  "method": "dct",  # 'lsb' or 'dct'
  "strength": 0.1   # 0.01-3.0
}

Response:
{
  "success": true,
  "artist_id": 123,
  "watermarking": {
    "enabled": true,
    "method": "dct",
    "strength": 0.1
  },
  "privacy_note": "Watermarking requires storing original images. If disabled, only feature vectors are stored."
}
```

**Get Preferences:**
```bash
GET /api/watermarking/preferences

Response:
{
  "artist_id": 123,
  "watermarking": {
    "enabled": true,
    "method": "dct",
    "strength": 0.1
  },
  "description": {
    "lsb": "LSB watermarking: Very invisible, less robust to transformations",
    "dct": "DCT watermarking: More robust to compression/resize, still invisible"
  }
}
```

---

## Privacy Rights

### GDPR Rights (EU/EEA Users)

| Right | Description | How to Exercise |
|-------|-------------|-----------------|
| **Access** | Request copy of your data | GET /api/privacy/my-data |
| **Rectification** | Correct inaccurate data | Update via account settings |
| **Erasure** | Delete your data | POST /api/privacy/delete-all |
| **Restriction** | Limit data processing | Update consent settings |
| **Portability** | Receive data in portable format | GET /api/consent/export |
| **Object** | Object to processing | POST /api/consent/withdraw |
| **Withdraw Consent** | Revoke consent | POST /api/consent/withdraw |
| **Complain** | Lodge complaint | Contact supervisory authority |

### CCPA Rights (California Users)

| Right | Description | How to Exercise |
|-------|-------------|-----------------|
| **Right to Know** | Know what data we collect | GET /api/privacy/my-data |
| **Right to Delete** | Delete personal information | POST /api/privacy/delete-all |
| **Right to Opt-Out** | Opt-out of data sale | Automatic (we don't sell data) |
| **Non-Discrimination** | Equal service regardless of choices | Guaranteed |

### Exercising Rights

**View All Data (GDPR/CCPA):**
```bash
GET /api/privacy/my-data

Response:
{
  "artist_id": 123,
  "artworks": [...],
  "detection_results": [...],
  "privacy_settings": {...},
  "consent_records": [...],
  "total_artworks": 10,
  "total_detections": 5
}
```

**Delete All Data (GDPR Right to Erasure / CCPA Right to Delete):**
```bash
POST /api/privacy/delete-all

Response:
{
  "success": true,
  "message": "All data has been deleted",
  "deleted": {
    "artworks": 10,
    "feature_vectors": 10,
    "detection_results": 5,
    "privacy_settings": 1
  },
  "timestamp": "2025-12-11T10:00:00Z"
}
```

---

## Legal Documents

### Terms of Service

**Access:**
```bash
GET /api/legal/terms-of-service

Response:
{
  "document": "terms_of_service",
  "version": "1.0",
  "last_updated": "2025-12-11",
  "url": "/legal_templates/TERMS_OF_SERVICE.md",
  "summary": "Terms of Service governs your use of ArtLockr"
}
```

**Key Points:**
- Account eligibility (13+, parental consent for <18)
- User content ownership (you retain all rights)
- Privacy-first storage by default
- Copyright detection disclaimer
- Limitation of liability
- Dispute resolution

### Privacy Policy

**Access:**
```bash
GET /api/legal/privacy-policy

Response:
{
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
```

### Cookie Policy

**Access:**
```bash
GET /api/legal/cookie-policy

Response:
{
  "document": "cookie_policy",
  "version": "1.0",
  "last_updated": "2025-12-11",
  "categories": {...},
  "opt_out_info": "You can manage cookie preferences at /api/cookies/preferences"
}
```

---

## API Usage

### Compliance Dashboard

**Get Complete Compliance Overview:**
```bash
GET /api/compliance/dashboard

Response:
{
  "user_id": "user123",
  "artist_id": 456,
  "compliance": {
    "consent": {
      "has_consents": true,
      "requires_update": false,
      "current_version": "1.0",
      "consents": {...}
    },
    "age_verification": {
      "is_verified": true,
      "age": 25
    },
    "watermarking": {
      "enabled": false,
      "method": "lsb",
      "strength": 1.0
    },
    "data_retention": {
      "mode": "features_only",
      "retention_period": "Until deletion",
      "auto_deletion": true
    }
  },
  "privacy_level": "maximum",
  "gdpr_compliant": true,
  "ccpa_compliant": true,
  "coppa_compliant": true
}
```

### Health Check

```bash
GET /api/compliance/health

Response:
{
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
  "timestamp": "2025-12-11T10:00:00Z"
}
```

---

## Implementation Checklist

### For Developers

- [ ] Implement consent banner on first visit
- [ ] Record consent decisions via `/api/consent/grant-batch`
- [ ] Check consent before enabling features (analytics, marketing, etc.)
- [ ] Respect cookie preferences
- [ ] Implement age gate for new users
- [ ] Provide easy access to privacy dashboard
- [ ] Include links to Terms of Service and Privacy Policy
- [ ] Handle consent expiration (re-prompt after 12 months)

### For Artists

- [ ] Review and accept Terms of Service
- [ ] Review Privacy Policy
- [ ] Set consent preferences
- [ ] Set cookie preferences
- [ ] Verify age (if required)
- [ ] Choose watermarking preference
- [ ] Review compliance dashboard regularly
- [ ] Exercise privacy rights as needed

---

## Summary

**ArtLockr Compliance:**

✅ **Full GDPR Compliance**
- Granular consent management
- Right to access, rectification, erasure, portability
- Data minimization (features-only by default)
- Consent versioning and expiration

✅ **Full CCPA Compliance**
- Right to know, delete, opt-out
- No sale of personal data
- Non-discrimination guarantee

✅ **Full COPPA Compliance**
- Age verification system
- Parental consent for under 13
- Limited data collection for children

✅ **Privacy-First Architecture**
- Features-only storage by default
- Immediate image deletion
- Cryptographic ownership proofs
- Complete transparency and control

**Contact:**
- Privacy inquiries: privacy@artlockr.com
- Data Protection Officer: dpo@artlockr.com
- Legal: legal@artlockr.com

---

**Version:** 1.0
**Last Updated:** December 11, 2025
