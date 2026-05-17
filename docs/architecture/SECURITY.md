# IncidentOS Backend - Security Documentation

## Overview

This document describes the security measures implemented in the IncidentOS backend to protect callback endpoints from unauthorized access.

**Last Updated:** 2026-05-16  
**Security Level:** MVP (API Key + IP Whitelisting)

---

## Security Threat Model

### Protected Endpoints

The following callback endpoints are protected from unauthorized access:

- `POST /callback/investigation-complete` - Receives RCA results from AI Engine
- `POST /callback/repository-parsed` (future)
- `POST /callback/dependencies-extracted` (future)
- `POST /callback/git-history-analyzed` (future)
- `POST /callback/fragility-complete` (future)
- `POST /callback/mentor-response` (future)

### Threats Mitigated

1. **Unauthorized Data Injection:** Prevents malicious clients from forging investigation results
2. **State Corruption:** Prevents premature completion of investigations
3. **Data Tampering:** Ensures only AI Engine can update investigation state
4. **Replay Attacks:** IP whitelisting prevents external replay attempts

---

## Security Implementation

### Two-Layer Authentication

The backend implements a **two-layer security model** for callback endpoints:

#### Layer 1: IP Whitelisting

**Purpose:** Network-level access control  
**Implementation:** `validateCallback()` middleware in `gateway.go`

**Behavior:**
- Extracts client IP from `RemoteAddr`
- For localhost deployment: Allows `127.0.0.1`, `::1`, `localhost`
- For separate deployment: Validates against `AI_ENGINE_IP` environment variable
- Rejects all other IPs with `403 Forbidden`

**Configuration:**
```bash
# For same-machine deployment (default)
# No configuration needed - localhost is automatically allowed

# For separate-machine deployment
AI_ENGINE_IP=192.168.1.100  # IP address of AI Engine server
```

#### Layer 2: API Key Authentication

**Purpose:** Application-level authentication  
**Implementation:** Validates `X-API-Key` HTTP header

**Behavior:**
- Checks for `X-API-Key` header in request
- Compares against `CALLBACK_API_KEY` environment variable
- Rejects requests with missing or invalid key with `401 Unauthorized`
- Logs all authentication attempts

**Configuration:**
```bash
# Generate a secure random key (recommended: 32+ characters)
CALLBACK_API_KEY=your-secure-random-key-here-change-in-production
```

**Generate Secure Key:**
```bash
# Linux/Mac
openssl rand -hex 32

# PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Required for production
CALLBACK_API_KEY=your-secure-random-key-here

# Required only if AI Engine is on a different machine
AI_ENGINE_IP=127.0.0.1
```

### AI Engine Configuration

The AI Engine must include the API key in all callback requests:

**Python Example:**
```python
import requests

headers = {
    "Content-Type": "application/json",
    "X-API-Key": os.getenv("CALLBACK_API_KEY")
}

response = requests.post(
    "http://backend:8080/callback/investigation-complete",
    json=payload,
    headers=headers
)
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-random-key-here" \
  -d '{"investigation_id": "inv_123", ...}'
```

---

## Security Logging

All authentication attempts are logged for audit purposes:

### Successful Authentication
```
[Security] Authenticated callback from IP: 127.0.0.1
```

### Failed Authentication - Invalid IP
```
[Security] Rejected callback from unauthorized IP: 192.168.1.50 (expected: 127.0.0.1)
```

### Failed Authentication - Missing API Key
```
[Security] Rejected callback without API key from IP: 127.0.0.1
```

### Failed Authentication - Invalid API Key
```
[Security] Rejected callback with invalid API key from IP: 127.0.0.1
```

### Configuration Warning
```
[Security Warning] CALLBACK_API_KEY not configured - callback endpoints are not fully secured
```

---

## Testing Security

### Test 1: Valid Request (Should Succeed)

```bash
# Set the API key
export CALLBACK_API_KEY="test-key-123"

# Start backend with API key
cd backend-go
CALLBACK_API_KEY=test-key-123 ./incidentos

# Make authenticated request
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{
    "investigation_id": "inv_test_123",
    "root_cause": "Test",
    "affected_services": [],
    "fragility_score": 5.0,
    "historical_correlation": "",
    "recommended_actions": []
  }'

# Expected: 200 OK
```

### Test 2: Missing API Key (Should Fail)

```bash
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: 401 Unauthorized
# Response: {"error": "Unauthorized: Missing API key"}
```

### Test 3: Invalid API Key (Should Fail)

```bash
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{...}'

# Expected: 401 Unauthorized
# Response: {"error": "Unauthorized: Invalid API key"}
```

### Test 4: Unauthorized IP (Should Fail)

```bash
# Set AI_ENGINE_IP to a different IP
AI_ENGINE_IP=192.168.1.100 ./incidentos

# Try to access from localhost
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "X-API-Key: test-key-123" \
  -d '{...}'

# Expected: 403 Forbidden
# Response: {"error": "Forbidden"}
```

---

## Deployment Scenarios

### Scenario 1: Development (Same Machine)

**Setup:**
- Backend and AI Engine on same machine
- Use localhost communication

**Configuration:**
```bash
# .env
CALLBACK_API_KEY=dev-key-not-for-production
# AI_ENGINE_IP not needed (localhost auto-allowed)
```

**Security Level:** Medium (API key only)

---

### Scenario 2: Production (Separate Machines)

**Setup:**
- Backend on server A (e.g., 192.168.1.10)
- AI Engine on server B (e.g., 192.168.1.20)

**Configuration:**
```bash
# Backend .env
CALLBACK_API_KEY=<strong-random-key-32-chars>
AI_ENGINE_IP=192.168.1.20

# AI Engine .env
CALLBACK_API_KEY=<same-strong-random-key>
BACKEND_URL=http://192.168.1.10:8080
```

**Security Level:** High (API key + IP whitelisting)

---

### Scenario 3: Docker Compose (Internal Network)

**Setup:**
- Backend and AI Engine in same Docker network
- Use service names for communication

**Configuration:**
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - CALLBACK_API_KEY=${CALLBACK_API_KEY}
      - AI_ENGINE_IP=ai-engine  # Docker service name
    networks:
      - internal

  ai-engine:
    environment:
      - CALLBACK_API_KEY=${CALLBACK_API_KEY}
      - BACKEND_URL=http://backend:8080
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

**Security Level:** High (isolated network + API key)

---

## Security Best Practices

### ✅ DO

1. **Use Strong API Keys**
   - Minimum 32 characters
   - Use cryptographically secure random generation
   - Rotate keys periodically

2. **Keep Keys Secret**
   - Never commit keys to version control
   - Use environment variables or secret management
   - Different keys for dev/staging/production

3. **Monitor Logs**
   - Review authentication failures regularly
   - Set up alerts for repeated failures
   - Track unusual access patterns

4. **Network Isolation**
   - Use private networks when possible
   - Firewall rules to restrict access
   - VPN for remote deployments

### ❌ DON'T

1. **Don't Use Weak Keys**
   - Avoid: "password", "123456", "test"
   - Avoid: Short keys (<16 characters)
   - Avoid: Predictable patterns

2. **Don't Expose Callback Endpoints**
   - Don't make them publicly accessible
   - Don't document them in public APIs
   - Don't include in frontend code

3. **Don't Ignore Warnings**
   - Fix "CALLBACK_API_KEY not configured" warnings
   - Don't disable security in production
   - Don't skip IP whitelisting

---

## Future Enhancements

### Phase 2: HMAC Signature Verification

**Benefits:**
- Cryptographic proof of authenticity
- Prevents replay attacks with timestamps
- No shared secret in transit

**Implementation:**
```go
// AI Engine signs request
signature := hmac.SHA256(timestamp + body, secret)
headers["X-Signature"] = signature
headers["X-Timestamp"] = timestamp

// Backend verifies signature
expectedSig := hmac.SHA256(timestamp + body, secret)
if signature != expectedSig || time.Now() - timestamp > 5min {
    reject()
}
```

### Phase 3: Mutual TLS (mTLS)

**Benefits:**
- Certificate-based authentication
- Encrypted communication
- No API keys to manage

**Requirements:**
- TLS certificates for both services
- Certificate authority setup
- Certificate rotation process

### Phase 4: OAuth 2.0 Client Credentials

**Benefits:**
- Industry-standard authentication
- Token-based with expiration
- Centralized auth server

**Requirements:**
- OAuth 2.0 server setup
- Token management
- Refresh token handling

---

## Compliance

### Security Standards Met

✅ **OWASP Top 10 (2021)**
- A01: Broken Access Control - Mitigated with IP + API key
- A02: Cryptographic Failures - API keys stored securely
- A07: Identification and Authentication Failures - Two-factor auth

✅ **CWE Top 25**
- CWE-306: Missing Authentication - Implemented
- CWE-862: Missing Authorization - Implemented

---

## Incident Response

### If API Key is Compromised

1. **Immediate Actions:**
   - Generate new API key
   - Update backend environment variable
   - Update AI Engine configuration
   - Restart both services

2. **Investigation:**
   - Review logs for unauthorized access
   - Identify compromised timeframe
   - Check for data tampering

3. **Prevention:**
   - Rotate keys more frequently
   - Implement key rotation automation
   - Add rate limiting

### If Unauthorized Access Detected

1. **Immediate Actions:**
   - Block offending IP at firewall level
   - Review all recent callback requests
   - Verify investigation data integrity

2. **Investigation:**
   - Trace source of unauthorized access
   - Check for other compromised endpoints
   - Review security logs

3. **Remediation:**
   - Strengthen IP whitelisting
   - Add rate limiting
   - Consider upgrading to HMAC signatures

---

## Support

For security concerns or questions:
- Review logs in backend console
- Check environment variable configuration
- Verify AI Engine is sending correct headers
- Test with curl commands above

---

**Document Version:** 1.0  
**Security Implementation:** Complete ✅  
**Status:** Production Ready with MVP Security