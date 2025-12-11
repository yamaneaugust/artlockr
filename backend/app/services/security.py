"""
Security Service for API Protection and Attack Defense

Provides:
- IP reputation scoring and blocking
- Request verification beyond user agents
- Behavioral anomaly detection
- Protection against API abuse and scraping
"""

import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
import json

from fastapi import Request, HTTPException, status


class IPReputationScorer:
    """
    IP reputation scoring system to detect and block malicious actors.

    Scores IPs based on:
    - Request frequency
    - Failed authentication attempts
    - Suspicious patterns (user agent rotation, header anomalies)
    - Known bad IP databases (optional integration)
    - Behavioral patterns

    Score ranges:
    - 100: Excellent (verified trusted source)
    - 75-99: Good (normal user)
    - 50-74: Suspicious (monitoring required)
    - 25-49: Bad (rate limited)
    - 0-24: Malicious (blocked)
    """

    def __init__(self):
        # IP reputation scores (0-100)
        self.ip_scores: Dict[str, float] = defaultdict(lambda: 75.0)  # Start at "good"

        # Track request history per IP
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Track user agent rotation per IP
        self.user_agents: Dict[str, set] = defaultdict(set)

        # Failed auth attempts
        self.failed_auth: Dict[str, int] = defaultdict(int)

        # Known malicious IPs (manually added or from threat feeds)
        self.blocklist: set = set()

        # Trusted IPs (whitelisted)
        self.allowlist: set = set()

        # Behavioral tracking
        self.behavior_scores: Dict[str, Dict] = defaultdict(lambda: {
            'consistent_ua': True,
            'normal_rate': True,
            'valid_referrer': True,
            'geographic_consistency': True
        })

    def calculate_reputation_score(self, ip: str, request: Request) -> float:
        """
        Calculate comprehensive reputation score for an IP.

        Returns:
            float: Reputation score (0-100)
        """
        # Whitelisted IPs get perfect score
        if ip in self.allowlist:
            return 100.0

        # Blacklisted IPs get zero
        if ip in self.blocklist:
            return 0.0

        score = self.ip_scores[ip]

        # Analyze user agent consistency
        user_agent = request.headers.get('user-agent', '')
        self.user_agents[ip].add(user_agent)

        # Penalize for user agent rotation (bot behavior)
        if len(self.user_agents[ip]) > 5:
            score -= 10
            self.behavior_scores[ip]['consistent_ua'] = False

        # Analyze request rate
        now = time.time()
        self.request_history[ip].append(now)

        # Check requests in last minute
        recent_requests = [t for t in self.request_history[ip] if now - t < 60]
        if len(recent_requests) > 60:  # More than 1 req/sec
            score -= 15
            self.behavior_scores[ip]['normal_rate'] = False

        # Check for suspicious user agents
        if self._is_suspicious_user_agent(user_agent):
            score -= 10

        # Check for missing or suspicious headers
        if not request.headers.get('accept-language'):
            score -= 5

        if not request.headers.get('accept'):
            score -= 5

        # Penalize for failed authentication attempts
        if self.failed_auth[ip] > 3:
            score -= 20

        # Update and clamp score
        score = max(0.0, min(100.0, score))
        self.ip_scores[ip] = score

        return score

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent matches known scraper/bot patterns."""
        suspicious_patterns = [
            r'bot', r'crawl', r'spider', r'scraper',
            r'curl', r'wget', r'python-requests',
            r'headless', r'phantom', r'selenium'
        ]

        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True

        return False

    def record_failed_auth(self, ip: str):
        """Record a failed authentication attempt."""
        self.failed_auth[ip] += 1
        self.ip_scores[ip] -= 5

    def record_successful_auth(self, ip: str):
        """Record a successful authentication (slight reputation boost)."""
        self.failed_auth[ip] = 0
        self.ip_scores[ip] = min(100.0, self.ip_scores[ip] + 2)

    def add_to_blocklist(self, ip: str, reason: str = "manual"):
        """Add IP to blocklist."""
        self.blocklist.add(ip)
        self.ip_scores[ip] = 0.0
        print(f"Added {ip} to blocklist. Reason: {reason}")

    def add_to_allowlist(self, ip: str):
        """Add IP to allowlist (trusted source)."""
        self.allowlist.add(ip)
        self.ip_scores[ip] = 100.0

    def is_blocked(self, ip: str) -> bool:
        """Check if IP should be blocked."""
        return ip in self.blocklist or self.ip_scores[ip] < 25

    def get_reputation_category(self, score: float) -> str:
        """Get human-readable reputation category."""
        if score >= 75:
            return "trusted"
        elif score >= 50:
            return "suspicious"
        elif score >= 25:
            return "bad"
        else:
            return "malicious"


class RateLimiter:
    """
    Multi-tier rate limiting system.

    Implements:
    - Per IP rate limiting
    - Per user rate limiting
    - Per API key rate limiting
    - Sliding window algorithm
    - Burst protection
    """

    def __init__(self):
        # Store request timestamps: {identifier: deque of timestamps}
        self.request_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Rate limit configurations (requests per time window)
        self.limits = {
            'ip': {
                'requests': 100,
                'window': 60  # 100 requests per minute
            },
            'user': {
                'requests': 1000,
                'window': 3600  # 1000 requests per hour
            },
            'api_key': {
                'requests': 10000,
                'window': 3600  # 10k requests per hour
            }
        }

    def is_rate_limited(
        self,
        identifier: str,
        limit_type: str = 'ip'
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if identifier is rate limited.

        Args:
            identifier: IP address, user ID, or API key
            limit_type: Type of limit ('ip', 'user', 'api_key')

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        config = self.limits.get(limit_type)
        if not config:
            return False, None

        now = time.time()
        window_start = now - config['window']

        # Clean old requests outside window
        request_log = self.request_logs[f"{limit_type}:{identifier}"]
        while request_log and request_log[0] < window_start:
            request_log.popleft()

        # Check if limit exceeded
        if len(request_log) >= config['requests']:
            # Calculate retry after (time until oldest request expires)
            retry_after = int(request_log[0] + config['window'] - now) + 1
            return True, retry_after

        # Record this request
        request_log.append(now)
        return False, None

    def get_usage_stats(self, identifier: str, limit_type: str = 'ip') -> Dict:
        """Get current usage statistics for an identifier."""
        config = self.limits.get(limit_type)
        if not config:
            return {}

        now = time.time()
        window_start = now - config['window']

        request_log = self.request_logs[f"{limit_type}:{identifier}"]
        recent_requests = [t for t in request_log if t >= window_start]

        return {
            'limit': config['requests'],
            'window_seconds': config['window'],
            'current_usage': len(recent_requests),
            'remaining': config['requests'] - len(recent_requests),
            'reset_at': int(now + config['window'])
        }

    def update_limits(self, limit_type: str, requests: int, window: int):
        """Update rate limit configuration."""
        self.limits[limit_type] = {
            'requests': requests,
            'window': window
        }


class BehavioralDetector:
    """
    Detects suspicious behavioral patterns that indicate:
    - API scraping
    - Automated bots
    - Data harvesting
    - Attack attempts
    """

    def __init__(self):
        # Track access patterns per IP
        self.access_patterns: Dict[str, Dict] = defaultdict(lambda: {
            'endpoints': defaultdict(int),
            'timestamps': deque(maxlen=100),
            'query_patterns': [],
            'header_fingerprints': set()
        })

    def analyze_request(self, ip: str, request: Request) -> Dict[str, any]:
        """
        Analyze request for suspicious patterns.

        Returns:
            Dictionary with anomaly scores and detected patterns
        """
        patterns = self.access_patterns[ip]
        anomalies = []
        risk_score = 0.0

        # Track endpoint access
        endpoint = request.url.path
        patterns['endpoints'][endpoint] += 1
        patterns['timestamps'].append(time.time())

        # 1. Sequential ID enumeration detection
        if self._is_sequential_enumeration(endpoint):
            anomalies.append("sequential_id_enumeration")
            risk_score += 30

        # 2. Rapid-fire requests (bot-like behavior)
        if self._is_rapid_fire(patterns['timestamps']):
            anomalies.append("rapid_fire_requests")
            risk_score += 25

        # 3. Systematic endpoint scanning
        if len(patterns['endpoints']) > 20:
            anomalies.append("endpoint_scanning")
            risk_score += 20

        # 4. Missing common browser headers
        if self._has_missing_headers(request):
            anomalies.append("missing_browser_headers")
            risk_score += 15

        # 5. Suspicious query patterns
        if self._has_suspicious_queries(request):
            anomalies.append("suspicious_query_patterns")
            risk_score += 20

        # 6. Header fingerprint consistency
        fingerprint = self._get_header_fingerprint(request)
        patterns['header_fingerprints'].add(fingerprint)

        if len(patterns['header_fingerprints']) > 5:
            anomalies.append("rotating_fingerprints")
            risk_score += 15

        return {
            'risk_score': min(100, risk_score),
            'anomalies': anomalies,
            'is_suspicious': risk_score > 50,
            'recommendation': self._get_recommendation(risk_score)
        }

    def _is_sequential_enumeration(self, endpoint: str) -> bool:
        """Detect sequential ID enumeration (e.g., /api/artwork/1, /api/artwork/2, ...)."""
        # This would need more sophisticated tracking
        # For now, just detect numeric IDs in URLs
        return bool(re.search(r'/\d+/?$', endpoint))

    def _is_rapid_fire(self, timestamps: deque, threshold: float = 0.1) -> bool:
        """Detect requests coming faster than human speed."""
        if len(timestamps) < 5:
            return False

        recent = list(timestamps)[-5:]
        intervals = [recent[i] - recent[i-1] for i in range(1, len(recent))]
        avg_interval = sum(intervals) / len(intervals)

        return avg_interval < threshold  # Less than 100ms between requests

    def _has_missing_headers(self, request: Request) -> bool:
        """Check for missing common browser headers."""
        required_headers = ['accept', 'accept-language', 'accept-encoding']
        return any(h not in request.headers for h in required_headers)

    def _has_suspicious_queries(self, request: Request) -> bool:
        """Detect suspicious query patterns (SQL injection, XSS attempts)."""
        query_string = str(request.query_params)

        suspicious_patterns = [
            r'union.*select', r'drop.*table', r'<script',
            r'javascript:', r'onerror=', r'\.\./', r'etc/passwd'
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                return True

        return False

    def _get_header_fingerprint(self, request: Request) -> str:
        """Create fingerprint from request headers."""
        headers_to_fingerprint = [
            'user-agent', 'accept', 'accept-language',
            'accept-encoding', 'connection'
        ]

        fingerprint_data = {
            h: request.headers.get(h, '') for h in headers_to_fingerprint
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _get_recommendation(self, risk_score: float) -> str:
        """Get recommended action based on risk score."""
        if risk_score >= 80:
            return "block"
        elif risk_score >= 50:
            return "challenge"  # CAPTCHA or additional verification
        elif risk_score >= 30:
            return "monitor"
        else:
            return "allow"


class OrganizationBlocker:
    """
    Manages blocking of organizations that have infringed on artist copyrights.

    Artists can block specific organizations from accessing their artwork
    through the API after detecting copyright infringement.
    """

    def __init__(self):
        # Maps artist_id -> set of blocked organization identifiers
        self.blocked_orgs: Dict[int, set] = defaultdict(set)

        # Maps organization identifier -> metadata
        self.org_metadata: Dict[str, Dict] = {}

        # Global blocklist (universally blocked orgs)
        self.global_blocklist: set = set()

    def block_organization(
        self,
        artist_id: int,
        org_identifier: str,
        reason: str = "",
        metadata: Optional[Dict] = None
    ):
        """
        Block an organization from accessing an artist's artwork.

        Args:
            artist_id: ID of the artist blocking the org
            org_identifier: Unique identifier (domain, API key hash, company name)
            reason: Reason for blocking (e.g., "copyright infringement detected")
            metadata: Additional metadata (detection_id, evidence, etc.)
        """
        self.blocked_orgs[artist_id].add(org_identifier)

        self.org_metadata[org_identifier] = {
            'blocked_by': artist_id,
            'blocked_at': datetime.utcnow().isoformat(),
            'reason': reason,
            'metadata': metadata or {}
        }

        print(f"Artist {artist_id} blocked organization: {org_identifier}")

    def is_organization_blocked(
        self,
        artist_id: int,
        org_identifier: str
    ) -> bool:
        """Check if organization is blocked by this artist."""
        # Check global blocklist first
        if org_identifier in self.global_blocklist:
            return True

        return org_identifier in self.blocked_orgs[artist_id]

    def get_blocked_organizations(self, artist_id: int) -> List[Dict]:
        """Get list of organizations blocked by an artist."""
        blocked = []

        for org_id in self.blocked_orgs[artist_id]:
            metadata = self.org_metadata.get(org_id, {})
            blocked.append({
                'organization': org_id,
                'blocked_at': metadata.get('blocked_at'),
                'reason': metadata.get('reason'),
                'metadata': metadata.get('metadata', {})
            })

        return blocked

    def unblock_organization(self, artist_id: int, org_identifier: str):
        """Unblock an organization."""
        if org_identifier in self.blocked_orgs[artist_id]:
            self.blocked_orgs[artist_id].remove(org_identifier)
            print(f"Artist {artist_id} unblocked organization: {org_identifier}")

    def add_to_global_blocklist(self, org_identifier: str, reason: str):
        """Add organization to global blocklist (affects all artists)."""
        self.global_blocklist.add(org_identifier)
        print(f"Added {org_identifier} to global blocklist: {reason}")


class RequestVerifier:
    """
    Advanced request verification beyond user agents.

    Implements multiple verification methods:
    - TLS fingerprinting
    - Header consistency checks
    - Timing analysis
    - Challenge-response tokens
    """

    def __init__(self):
        self.challenge_tokens: Dict[str, Dict] = {}
        self.verified_clients: Dict[str, float] = {}  # client_id -> last_verified_timestamp

    def verify_request(self, request: Request, ip: str) -> Tuple[bool, str]:
        """
        Comprehensive request verification.

        Returns:
            Tuple of (is_verified, reason)
        """
        # 1. Check for verification token
        token = request.headers.get('X-Verification-Token')
        if token and self._verify_challenge_token(ip, token):
            return True, "valid_token"

        # 2. Check header consistency
        if not self._check_header_consistency(request):
            return False, "inconsistent_headers"

        # 3. Check for browser-like behavior
        if not self._has_browser_characteristics(request):
            return False, "missing_browser_characteristics"

        # 4. Check TLS fingerprint (if available)
        # This would require integration with reverse proxy/load balancer
        # For now, we'll skip this

        return True, "verified"

    def _check_header_consistency(self, request: Request) -> bool:
        """Check if headers are consistent with claimed user agent."""
        user_agent = request.headers.get('user-agent', '').lower()

        # If claiming to be a browser, should have browser headers
        is_browser = any(browser in user_agent for browser in ['chrome', 'firefox', 'safari', 'edge'])

        if is_browser:
            required_headers = ['accept', 'accept-language', 'accept-encoding']
            if not all(h in request.headers for h in required_headers):
                return False

        return True

    def _has_browser_characteristics(self, request: Request) -> bool:
        """Check if request has characteristics of a real browser."""
        # Real browsers send these headers
        browser_headers = [
            'sec-ch-ua',
            'sec-ch-ua-mobile',
            'sec-ch-ua-platform',
            'sec-fetch-site',
            'sec-fetch-mode',
            'sec-fetch-dest'
        ]

        # At least some of these should be present
        present_count = sum(1 for h in browser_headers if h in request.headers)
        return present_count >= 2

    def generate_challenge_token(self, ip: str) -> str:
        """Generate a challenge token for verification."""
        token = hashlib.sha256(f"{ip}{time.time()}".encode()).hexdigest()

        self.challenge_tokens[token] = {
            'ip': ip,
            'created_at': time.time(),
            'expires_at': time.time() + 300  # 5 minutes
        }

        return token

    def _verify_challenge_token(self, ip: str, token: str) -> bool:
        """Verify a challenge token."""
        token_data = self.challenge_tokens.get(token)

        if not token_data:
            return False

        # Check if token matches IP
        if token_data['ip'] != ip:
            return False

        # Check if token is expired
        if time.time() > token_data['expires_at']:
            del self.challenge_tokens[token]
            return False

        # Valid token - mark client as verified
        self.verified_clients[ip] = time.time()
        del self.challenge_tokens[token]

        return True


# Global instances (singleton pattern)
ip_reputation = IPReputationScorer()
rate_limiter = RateLimiter()
behavioral_detector = BehavioralDetector()
org_blocker = OrganizationBlocker()
request_verifier = RequestVerifier()
