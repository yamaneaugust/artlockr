# Security & API Gating Documentation

## Overview

ArtLock implements **enterprise-grade security** with multiple layers of protection against:
- API abuse and scraping
- Adversarial attacks on the ML model
- Copyright infringement through unauthorized access
- Automated bots and malicious actors
- Data harvesting and model stealing

---

## Table of Contents

1. [Multi-Layer Security Architecture](#multi-layer-security-architecture)
2. [IP Reputation System](#ip-reputation-system)
3. [Rate Limiting](#rate-limiting)
4. [Behavioral Detection](#behavioral-detection)
5. [AI Attack Defense](#ai-attack-defense)
6. [Organization Blocking](#organization-blocking)
7. [Request Verification](#request-verification)
8. [API Usage](#api-usage)
9. [Best Practices](#best-practices)

---

## Multi-Layer Security Architecture

ArtLock uses **5 layers of defense**:

```
┌─────────────────────────────────────────┐
│  Layer 1: IP Reputation Scoring         │  ← Scores IPs (0-100), blocks malicious
├─────────────────────────────────────────┤
│  Layer 2: Rate Limiting                 │  ← Per IP, User, API key limits
├─────────────────────────────────────────┤
│  Layer 3: Behavioral Analysis           │  ← Detects suspicious patterns
├─────────────────────────────────────────┤
│  Layer 4: Request Verification          │  ← Validates beyond user agents
├─────────────────────────────────────────┤
│  Layer 5: AI Attack Defense             │  ← Protects ML model from adversarial attacks
└─────────────────────────────────────────┘
```

All layers work together to provide comprehensive protection while maintaining fast response times (<10ms security overhead).

---

## IP Reputation System

### How It Works

Every IP is assigned a **reputation score (0-100)**:

| Score | Category | Action |
|-------|----------|--------|
| 75-100 | Trusted | Full access |
| 50-74 | Suspicious | Monitored, may require verification |
| 25-49 | Bad | Rate limited, additional checks |
| 0-24 | Malicious | **BLOCKED** |

### Reputation Factors

IPs are scored based on:

1. **Request Frequency** (-15 if >60 req/min)
2. **User Agent Rotation** (-10 if >5 different UAs)
3. **Failed Authentication** (-5 per failed attempt)
4. **Suspicious User Agents** (-10 if bot-like)
5. **Missing Headers** (-5 for each missing common header)

**Example:**
```
IP: 192.168.1.100
Starting score: 75

Actions:
- Sent 70 requests in 1 minute → -15 (60)
- Used 6 different user agents → -10 (50)
- Missing accept-language header → -5 (45)
- 1 failed login attempt → -5 (40)

Final score: 40 → Category: Bad (rate limited)
```

### API Endpoints

**Check IP Reputation:**
```bash
GET /api/ip-reputation/{ip}

Response:
{
  "ip": "192.168.1.100",
  "reputation_score": 40.0,
  "category": "bad",
  "request_count": 127,
  "failed_auth_count": 1,
  "is_blocked": false,
  "in_allowlist": false,
  "in_blocklist": false,
  "user_agents_count": 6
}
```

**Manually Block IP:**
```bash
POST /api/ip-reputation/block/{ip}?reason=manual

Response:
{
  "success": true,
  "message": "IP 192.168.1.100 has been blocked",
  "ip": "192.168.1.100",
  "reason": "manual"
}
```

**Whitelist IP (Trusted Source):**
```bash
POST /api/ip-reputation/allow/{ip}

Response:
{
  "success": true,
  "message": "IP 192.168.1.100 has been added to allowlist",
  "ip": "192.168.1.100",
  "reputation_score": 100.0
}
```

---

## Rate Limiting

### Three-Tier Rate Limiting

ArtLock implements rate limiting at **3 levels**:

| Level | Limit | Window | Use Case |
|-------|-------|--------|----------|
| **IP** | 100 req | 60s | Per IP address |
| **User** | 1000 req | 3600s | Per authenticated user |
| **API Key** | 10000 req | 3600s | Per API key |

### Endpoint-Specific Limits

Different endpoints have different limits:

| Endpoint Pattern | Limit | Reason |
|-----------------|-------|--------|
| `/api/upload` | 10/min | Expensive operation |
| `/api/detect` | 30/min | Moderate cost |
| `/api/privacy` | 20/min | Sensitive operations |
| **Default** | 100/min | Standard operations |

### Rate Limit Headers

All responses include rate limit info:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1699999999
```

### Rate Limit Exceeded Response

```http
HTTP 429 Too Many Requests
Retry-After: 45

{
  "error": "Rate limit exceeded",
  "retry_after": 45,
  "message": "Too many requests. Please try again in 45 seconds."
}
```

### API Endpoints

**Check Your Rate Limit Status:**
```bash
GET /api/rate-limit/status

Response:
{
  "ip": "192.168.1.100",
  "ip_rate_limit": {
    "limit": 100,
    "window_seconds": 60,
    "current_usage": 27,
    "remaining": 73,
    "reset_at": 1699999999
  },
  "timestamp": "2025-12-11T10:00:00"
}
```

**View Rate Limit Configuration:**
```bash
GET /api/rate-limit/config

Response:
{
  "rate_limits": {
    "ip": {"requests": 100, "window": 60},
    "user": {"requests": 1000, "window": 3600},
    "api_key": {"requests": 10000, "window": 3600}
  }
}
```

---

## Behavioral Detection

### Anomaly Detection

The behavioral detector identifies **6 types of suspicious patterns**:

#### 1. Sequential ID Enumeration
**Pattern:** `/api/artwork/1`, `/api/artwork/2`, `/api/artwork/3`...
**Risk:** +30
**Indicates:** Systematic data scraping

#### 2. Rapid-Fire Requests
**Pattern:** Requests <100ms apart
**Risk:** +25
**Indicates:** Automated bot behavior

#### 3. Endpoint Scanning
**Pattern:** Accessing >20 different endpoints
**Risk:** +20
**Indicates:** API reconnaissance

#### 4. Missing Browser Headers
**Pattern:** No `accept`, `accept-language`, or `accept-encoding`
**Risk:** +15
**Indicates:** Non-browser client (likely bot)

#### 5. Suspicious Query Patterns
**Pattern:** SQL injection, XSS attempts, path traversal
**Risk:** +20
**Indicates:** Attack attempt

#### 6. Rotating Fingerprints
**Pattern:** >5 different header fingerprints from same IP
**Risk:** +15
**Indicates:** Header spoofing

### Risk Scores

| Risk Score | Recommendation | Action |
|------------|---------------|--------|
| 0-29 | Allow | Normal processing |
| 30-49 | Monitor | Log for analysis |
| 50-79 | Challenge | Require additional verification |
| 80-100 | **Block** | Deny access |

### Example Detection

```json
{
  "risk_score": 75,
  "anomalies": [
    "rapid_fire_requests",
    "endpoint_scanning",
    "missing_browser_headers"
  ],
  "is_suspicious": true,
  "recommendation": "challenge"
}
```

### API Endpoint

**Analyze IP Behavior:**
```bash
GET /api/security/behavioral-analysis/{ip}

Response:
{
  "ip": "192.168.1.100",
  "endpoints_accessed": {
    "/api/detect": 45,
    "/api/upload": 12,
    "/api/privacy/my-data": 3
  },
  "total_requests": 60,
  "unique_endpoints": 3,
  "header_fingerprints": 2
}
```

---

## AI Attack Defense

### Threat Model

ArtLock defends against **5 types of AI attacks**:

1. **FGSM** (Fast Gradient Sign Method)
2. **PGD** (Projected Gradient Descent)
3. **DeepFool**
4. **Feature Poisoning**
5. **Query-Based Model Stealing**

### Defense Mechanisms

#### 1. Adversarial Perturbation Detection

Detects modified images designed to fool the model:

**Detection Methods:**
- **Pixel Statistics Analysis**: Detects unusual pixel distributions
- **Gradient Magnitude Analysis**: Finds abnormal image gradients
- **Frequency Domain Analysis**: Detects high-frequency noise injection
- **Feature Space Analysis**: Identifies abnormal feature vectors
- **Noise Pattern Analysis**: Detects structured adversarial noise

**Anomaly Scores:**
```json
{
  "pixel_anomaly": 0.3,
  "gradient_anomaly": 0.8,  ← High! Likely adversarial
  "frequency_anomaly": 0.6,
  "feature_anomaly": 0.4,
  "noise_anomaly": 0.7,
  "overall_probability": 0.56  → DETECTED
}
```

#### 2. Query Pattern Analysis

Detects systematic attacks through query patterns:

**Attack Patterns:**
- **Feature Probing**: Systematically exploring feature space
- **Gradient Estimation**: Queries with small perturbations (>0.99 similarity)
- **High-Frequency Queries**: >30 queries/minute
- **Boundary Exploration**: Finding decision boundaries

**Detection Example:**
```json
{
  "patterns_detected": [
    "gradient_estimation",
    "high_frequency_queries"
  ],
  "risk_score": 70
}
```

#### 3. Input Validation

**Checks:**
- File format validation (JPEG, PNG, WEBP, BMP only)
- Image size limits (max 4096x4096)
- File size limits (max 10MB)
- Minimum size (min 50x50 to prevent attacks)
- Corruption detection

**Invalid Image Response:**
```json
{
  "error": "Invalid image",
  "reason": "Image too large (5000x5000), max (4096, 4096)"
}
```

#### 4. Robust Feature Extraction

**Defense Techniques:**
- **Input Normalization**: Standardizes inputs
- **Feature Randomization**: Adds small random noise
- **Ensemble Predictions**: Averages multiple extractions
- **Gradient Masking**: Makes gradient estimation harder

**Usage:**
```python
# Robust extraction with ensemble (3 samples)
features = robust_extractor.extract_robust_features(
    image=image,
    use_ensemble=True  # More robust but ~3x slower
)
```

### When Adversarial Attack is Detected

```http
HTTP 403 Forbidden

{
  "error": "Adversarial attack detected",
  "anomaly_scores": {
    "gradient_anomaly": 0.8,
    "frequency_anomaly": 0.6,
    "overall_probability": 0.56
  },
  "message": "Image contains suspicious perturbations"
}
```

---

## Organization Blocking

### Use Case

After detecting copyright infringement, **block the infringing organization** from accessing your artwork through the API.

### Organization Identifiers

Organizations can be identified by:

1. **API Key Hash**: SHA-256 hash of their API key
2. **Domain**: Extracted from `Referer` header
3. **Custom Header**: `X-Organization-ID`

### Block Organization

**API Endpoint:**
```bash
POST /api/block-organization

Body:
{
  "organization_identifier": "example.com",
  "reason": "copyright infringement detected",
  "detection_id": 123  # Optional: link to detection result
}

Response:
{
  "success": true,
  "message": "Organization 'example.com' has been blocked",
  "artist_id": 456,
  "organization": "example.com",
  "reason": "copyright infringement detected",
  "blocked_at": "2025-12-11T10:00:00"
}
```

### View Blocked Organizations

```bash
GET /api/blocked-organizations

Response:
{
  "artist_id": 456,
  "total_blocked": 3,
  "blocked_organizations": [
    {
      "organization": "example.com",
      "blocked_at": "2025-12-11T10:00:00",
      "reason": "copyright infringement detected",
      "metadata": {
        "detection_id": 123,
        "matches_found": 5,
        "scan_date": "2025-12-11T09:30:00"
      }
    }
  ]
}
```

### Unblock Organization

```bash
POST /api/unblock-organization

Body:
{
  "organization_identifier": "example.com"
}

Response:
{
  "success": true,
  "message": "Organization 'example.com' has been unblocked",
  "artist_id": 456,
  "organization": "example.com"
}
```

### How Blocking Works

When a blocked organization tries to access your artwork:

```http
HTTP 403 Forbidden

{
  "error": "Access denied",
  "reason": "Organization blocked by artist",
  "organization": "example.com",
  "blocked_at": "2025-12-11T10:00:00"
}
```

---

## Request Verification

### Beyond User Agents

Traditional API protection relies on User-Agent headers, which are **easily spoofed**. ArtLock uses **advanced verification**.

### Verification Methods

#### 1. Header Consistency Checks
- Validates headers match claimed user agent
- Browsers must have `accept`, `accept-language`, `accept-encoding`
- Detects inconsistencies (e.g., "Chrome" UA without Chrome headers)

#### 2. Browser Characteristic Detection
- Looks for browser-specific headers:
  - `sec-ch-ua`, `sec-ch-ua-mobile`, `sec-ch-ua-platform`
  - `sec-fetch-site`, `sec-fetch-mode`, `sec-fetch-dest`
- Real browsers send at least 2 of these

#### 3. Challenge-Response Tokens
- Generate verification tokens for trusted clients
- Tokens valid for 5 minutes
- Must be included in `X-Verification-Token` header

### Generate Verification Token

```bash
POST /api/security/generate-token

Response:
{
  "token": "a1b2c3d4e5f6...",
  "expires_at": 1699999999,
  "usage": "Include this token in the 'X-Verification-Token' header",
  "example": {
    "headers": {
      "X-Verification-Token": "a1b2c3d4e5f6..."
    }
  }
}
```

### Using Verification Token

```bash
GET /api/detect-copyright/123
Headers:
  X-Verification-Token: a1b2c3d4e5f6...

# Request verified ✅
```

---

## API Usage

### Security Analytics

**Get Overall Security Stats:**
```bash
GET /api/security/analytics

Response:
{
  "total_tracked_ips": 1523,
  "blocked_ips": 47,
  "suspicious_ips": 89,
  "trusted_ips": 12,
  "top_blocked_ips": [
    {
      "ip": "192.168.1.100",
      "reputation_score": 15.0,
      "category": "malicious"
    }
  ],
  "detected_attack_patterns": [
    "Endpoint scanning from 192.168.1.100",
    "Rapid-fire requests from 10.0.0.5"
  ],
  "total_organizations_blocked": 23,
  "timestamp": "2025-12-11T10:00:00"
}
```

### Security Health Check

```bash
GET /api/security/health

Response:
{
  "status": "healthy",
  "services": {
    "ip_reputation": "active",
    "rate_limiter": "active",
    "behavioral_detector": "active",
    "organization_blocker": "active",
    "request_verifier": "active"
  },
  "statistics": {
    "tracked_ips": 1523,
    "blocked_ips": 47,
    "allowed_ips": 12,
    "active_rate_limits": 234
  }
}
```

---

## Best Practices

### For Artists

1. **Monitor Security Analytics**
   - Check `/api/security/analytics` regularly
   - Review top blocked IPs
   - Identify attack patterns

2. **Block Infringers Immediately**
   - After detecting copyright infringement, block the organization
   - Include `detection_id` for evidence trail

3. **Whitelist Trusted Sources**
   - Add your own IPs to allowlist
   - Whitelist legitimate AI research organizations (if desired)

4. **Review Blocked Organizations**
   - Periodically review `/api/blocked-organizations`
   - Unblock if copyright dispute is resolved

### For Developers

1. **Implement Proper Authentication**
   - Don't rely only on user agents
   - Use API keys or OAuth
   - Include organization identifiers in headers

2. **Respect Rate Limits**
   - Monitor `X-RateLimit-Remaining` header
   - Implement exponential backoff on 429 responses
   - Cache results when possible

3. **Handle Security Responses**
   ```python
   response = requests.get(url)

   if response.status_code == 429:
       retry_after = int(response.headers['Retry-After'])
       time.sleep(retry_after)
       # Retry request

   elif response.status_code == 403:
       # IP blocked or org blocked
       # Check response body for reason
       error = response.json()
       if error.get('reason') == 'Organization blocked by artist':
           # Contact artist to resolve copyright issue
   ```

4. **Use Verification Tokens**
   - For high-volume applications, generate verification tokens
   - Include in all requests for faster processing

### For System Administrators

1. **Configure Strict Mode** (optional)
   ```python
   app.add_middleware(SecurityMiddleware, enable_strict_mode=True)
   ```
   - Blocks all unverified requests
   - Blocks all suspicious behavior (risk >50)

2. **Adjust Rate Limits**
   ```python
   from backend.app.services.security import rate_limiter

   # Increase limits for premium users
   rate_limiter.update_limits('api_key', requests=50000, window=3600)
   ```

3. **Monitor Logs**
   - Track blocked IPs
   - Identify attack patterns
   - Adjust thresholds as needed

4. **Integration with Threat Feeds** (future)
   - Integrate with external IP reputation services
   - Automatically block known malicious IPs

---

## Security Performance

### Overhead

Security checks add minimal latency:

| Layer | Overhead |
|-------|----------|
| IP Reputation | ~1ms |
| Rate Limiting | ~0.5ms |
| Behavioral Analysis | ~2ms |
| Request Verification | ~1ms |
| **Total** | **~5ms** |

For a 160ms detection request, security adds only **3% overhead**.

### Scalability

- **In-memory storage**: Handles 10,000+ concurrent IPs
- **O(1) lookups**: All operations use hash maps
- **Automatic cleanup**: Old data expires automatically

**For high-scale deployments:**
- Use Redis for shared rate limiting across servers
- Use distributed IP reputation database
- Enable caching for verification tokens

---

## Threat Response Workflow

```mermaid
Request → IP Reputation → Rate Limit → Behavioral → Verification → AI Defense → Response
            ↓ BLOCK         ↓ 429         ↓ BLOCK      ↓ 401        ↓ 403
```

**Example Flow:**

1. **Request arrives** from IP `192.168.1.100`
2. **IP Reputation**: Score = 85 (Trusted) ✅
3. **Rate Limit**: 45/100 used ✅
4. **Behavioral**: Risk = 25 (Low) ✅
5. **Verification**: Headers consistent ✅
6. **AI Defense**: Image analysis → No adversarial perturbations ✅
7. **Response**: HTTP 200 with detection results

**Attack Example:**

1. **Request arrives** from IP `10.0.0.5`
2. **IP Reputation**: Score = 20 (Malicious) ❌
3. **Response**: HTTP 403 Forbidden

---

## Summary

ArtLock provides **enterprise-grade security** with:

✅ **IP Reputation System** - Scores and blocks malicious IPs
✅ **Multi-Tier Rate Limiting** - Per IP, user, and API key
✅ **Behavioral Detection** - Identifies 6 types of suspicious patterns
✅ **AI Attack Defense** - Protects against adversarial attacks
✅ **Organization Blocking** - Block copyright infringers
✅ **Request Verification** - Beyond user agent spoofing
✅ **<5ms Overhead** - Minimal performance impact
✅ **Comprehensive APIs** - Monitor and manage security

**Result**: Artists can confidently protect their work while the system automatically defends against abuse, scraping, and attacks.
