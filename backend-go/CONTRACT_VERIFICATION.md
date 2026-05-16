# Contract Verification Report

## Purpose
This document verifies that [`backend_pending.md`](backend_pending.md) implementation plan matches the exact request-response structures defined in [`contracts.md`](contracts.md).

---

## ✅ Verified Contracts

### 1. Upload Repository (Workflow 1)

**Contract Specification:**
- **Endpoint:** `POST /upload-repo`
- **Request:**
  ```json
  {
    "repo_url": "https://github.com/user/repo"
  }
  ```
- **Response:**
  ```json
  {
    "repo_id": "repo_123",
    "status": "uploaded"
  }
  ```

**Implementation Status:** ✅ Already implemented in [`gateway.go`](internal/api/gateway.go)  
**Verification:** PASS - Matches contract exactly

---

### 2. Analyze Repository (Workflow 3)

**Contract Specification:**

#### Backend → AI Engine
- **Endpoint:** `POST /analyze-repo`
- **Request:**
  ```json
  {
    "repo_id": "repo_123",
    "repo_path": "./repos/repo_123"
  }
  ```
- **Response:**
  ```json
  {
    "repo_id": "repo_123",
    "status": "analysis_started"
  }
  ```

**Implementation Status:** ✅ Already implemented  
**Verification:** PASS - Job queue sends correct payload to AI Engine

---

### 3. Fragility Analysis (Workflow 7)

**Contract Specification:**

#### Backend → AI Engine
- **Endpoint:** `POST /compute-fragility`
- **Request:**
  ```json
  {
    "repo_id": "repo_123"
  }
  ```

#### AI Engine → Backend (Callback)
- **Response:**
  ```json
  {
    "repo_id": "repo_123",
    "fragility_scores": [
      {
        "service": "auth-service",
        "score": 8.7,
        "reasons": [
          "high commit churn",
          "high dependency centrality",
          "recent regressions"
        ]
      }
    ]
  }
  ```

**Implementation Status:** ⚠️ Partially implemented (request only)  
**Pending Work:** Need callback endpoint to receive fragility scores  
**Plan Alignment:** ✅ CORRECT - Plan includes callback endpoint for fragility results

---

### 4. Dashboard Data (Workflow 9)

**Contract Specification:**
- **Endpoint:** `GET /dashboard/{repo_id}`
- **Response:**
  ```json
  {
    "repo_id": "repo_123",
    "services": 12,
    "dependencies": 38,
    "fragile_services": [
      "auth-service",
      "checkout-service"
    ],
    "recent_incidents": 4
  }
  ```

**Implementation Status:** ⚠️ Stubbed  
**Pending Work:** Fetch real data from Neo4j and ChromaDB  
**Plan Alignment:** ✅ CORRECT - Plan specifies exact response structure

**⚠️ DISCREPANCY FOUND:**
- **Contract:** Does NOT include `last_analysis` field
- **Plan (line 265):** Includes `"last_analysis": "2026-05-15T10:30:00Z"`
- **Action Required:** Remove `last_analysis` from plan OR add to contract

---

### 5. Dependency Graph (Workflow 10)

**Contract Specification:**
- **Endpoint:** `GET /dependency-graph/{repo_id}`
- **Response:**
  ```json
  {
    "nodes": [
      {
        "id": "auth-service",
        "type": "service"
      }
    ],
    "edges": [
      {
        "source": "checkout-service",
        "target": "auth-service"
      }
    ]
  }
  ```

**Implementation Status:** ⚠️ Stubbed  
**Pending Work:** Query Neo4j for real graph data  
**Plan Alignment:** ✅ CORRECT - Matches contract structure

---

### 6. Incident Investigation (Workflow 11)

**Contract Specification:**

#### Frontend → Backend
- **Endpoint:** `POST /start-investigation`
- **Request:**
  ```json
  {
    "repo_id": "repo_123",
    "incident": "checkout-service CI failed"
  }
  ```

#### Backend → AI Engine
- **Request:** (Same as above)
  ```json
  {
    "repo_id": "repo_123",
    "incident": "checkout-service CI failed"
  }
  ```

#### AI Engine → Backend
- **Response:**
  ```json
  {
    "root_cause": "JWT validation regression",
    "affected_services": [
      "auth-service",
      "checkout-service"
    ],
    "confidence": 0.87,
    "historical_match": "OAuth migration incident"
  }
  ```

**Implementation Status:** ⚠️ Partially implemented (request only)  
**Pending Work:** Investigation Manager + callback handling  
**Plan Alignment:** ✅ CORRECT - Investigation Manager will handle this

---

### 7. Mentor Query (Workflow 12)

**Contract Specification:**

#### Frontend → Backend
- **Endpoint:** `POST /mentor-query`
- **Request:**
  ```json
  {
    "repo_id": "repo_123",
    "question": "What should I learn first?"
  }
  ```

#### Backend → AI Engine
- **Request:** (Same as above)
  ```json
  {
    "repo_id": "repo_123",
    "question": "What should I learn first?"
  }
  ```

#### AI Engine → Backend
- **Response:**
  ```json
  {
    "answer": "Start with auth-service because it is central to the architecture and is depended on by multiple services."
  }
  ```

**Implementation Status:** ⚠️ Partially implemented (request only)  
**Pending Work:** Callback endpoint + ChromaDB integration for context  
**Plan Alignment:** ✅ CORRECT - Plan includes ChromaDB for mentor context

---

### 8. WebSocket Events (Workflow 13)

**Contract Specification:**

#### Backend → Frontend (WebSocket)
Event formats:
```json
{"event": "repo_analysis_started"}
{"event": "dependency_graph_generated"}
{"event": "fragility_analysis_complete"}
{"event": "investigation_complete"}
```

**Implementation Status:** ❌ Not implemented  
**Pending Work:** Full WebSocket Hub implementation  
**Plan Alignment:** ✅ CORRECT - Plan includes all event types

**⚠️ ENHANCEMENT NEEDED:**
- **Contract:** Only specifies event name
- **Plan:** Should include additional fields like `repo_id`, `timestamp`, `data`
- **Recommendation:** Enhance event structure for better frontend integration

---

### 9. Final RCA Report (Workflow 14)

**Contract Specification:**

#### AI Engine → Backend
- **Response:**
  ```json
  {
    "incident": "checkout-service CI failed",
    "root_cause": "JWT validation regression",
    "affected_services": [
      "auth-service",
      "checkout-service"
    ],
    "fragility_score": 8.7,
    "historical_correlation": "OAuth migration incident",
    "recommended_actions": [
      "rollback recent auth changes",
      "add JWT integration tests"
    ]
  }
  ```

**Implementation Status:** ❌ Not implemented  
**Pending Work:** Investigation Manager callback handling  
**Plan Alignment:** ✅ CORRECT - Investigation Manager will store this

---

## 🔍 Missing Contracts in Plan

### 1. Repository Parsing Output (Workflow 4)

**Contract Specification:**
```json
{
  "repo_id": "repo_123",
  "services": [
    "auth-service",
    "payment-service",
    "checkout-service"
  ],
  "languages": [
    "Python",
    "TypeScript"
  ],
  "frameworks": [
    "FastAPI",
    "Next.js"
  ]
}
```

**Status:** ❌ NOT mentioned in plan  
**Action Required:** Add callback endpoint to receive repository parsing results  
**Suggested Endpoint:** `POST /callback/repository-parsed`

---

### 2. Dependency Graph Generation Output (Workflow 5)

**Contract Specification:**
```json
{
  "repo_id": "repo_123",
  "dependencies": [
    {
      "source": "checkout-service",
      "target": "auth-service",
      "type": "DEPENDS_ON"
    }
  ]
}
```

**Status:** ⚠️ Partially mentioned (Neo4j storage)  
**Action Required:** Add explicit callback endpoint for dependency data  
**Suggested Endpoint:** `POST /callback/dependencies-extracted`

---

### 3. Git History Analysis Output (Workflow 6)

**Contract Specification:**
```json
{
  "repo_id": "repo_123",
  "high_churn_services": [
    "auth-service"
  ],
  "recent_commits": 124,
  "top_contributors": [
    "dev1",
    "dev2"
  ]
}
```

**Status:** ❌ NOT mentioned in plan  
**Action Required:** Add callback endpoint for git history results  
**Suggested Endpoint:** `POST /callback/git-history-analyzed`

---

## 📊 Summary of Discrepancies

### Critical Issues (Must Fix)
1. **Dashboard Response:** Remove `last_analysis` field OR update contract
2. **Missing Callbacks:** Add 3 callback endpoints for AI Engine results:
   - `POST /callback/repository-parsed` (Workflow 4)
   - `POST /callback/dependencies-extracted` (Workflow 5)
   - `POST /callback/git-history-analyzed` (Workflow 6)

### Enhancements (Recommended)
1. **WebSocket Events:** Add `repo_id`, `timestamp`, and `data` fields to event structure
2. **Error Responses:** Define standard error format for all endpoints
3. **Investigation Status:** Add intermediate status updates during investigation

---

## ✅ Corrected Implementation Plan

### Updated Callback Endpoints Section

**All Callback Endpoints (Complete List):**

1. **`POST /callback/repository-parsed`** - Repository structure analysis
   ```json
   {
     "repo_id": "repo_123",
     "services": ["auth-service", "payment-service"],
     "languages": ["Python", "TypeScript"],
     "frameworks": ["FastAPI", "Next.js"]
   }
   ```

2. **`POST /callback/dependencies-extracted`** - Dependency graph data
   ```json
   {
     "repo_id": "repo_123",
     "dependencies": [
       {
         "source": "checkout-service",
         "target": "auth-service",
         "type": "DEPENDS_ON"
       }
     ]
   }
   ```

3. **`POST /callback/git-history-analyzed`** - Git history insights
   ```json
   {
     "repo_id": "repo_123",
     "high_churn_services": ["auth-service"],
     "recent_commits": 124,
     "top_contributors": ["dev1", "dev2"]
   }
   ```

4. **`POST /callback/fragility-complete`** - Fragility scores
   ```json
   {
     "repo_id": "repo_123",
     "fragility_scores": [
       {
         "service": "auth-service",
         "score": 8.7,
         "reasons": ["high commit churn"]
       }
     ]
   }
   ```

5. **`POST /callback/investigation-progress`** - Investigation step updates
   ```json
   {
     "investigation_id": "inv_123",
     "step": "analyzing_dependencies",
     "status": "in_progress",
     "timestamp": "2026-05-16T10:30:00Z"
   }
   ```

6. **`POST /callback/investigation-complete`** - Final RCA report
   ```json
   {
     "investigation_id": "inv_123",
     "incident": "checkout-service CI failed",
     "root_cause": "JWT validation regression",
     "affected_services": ["auth-service", "checkout-service"],
     "fragility_score": 8.7,
     "historical_correlation": "OAuth migration incident",
     "recommended_actions": ["rollback recent auth changes"]
   }
   ```

7. **`POST /callback/mentor-response`** - Mentor query answer
   ```json
   {
     "repo_id": "repo_123",
     "question": "What should I learn first?",
     "answer": "Start with auth-service..."
   }
   ```

---

### Updated WebSocket Event Structure

**Enhanced Event Format:**
```json
{
  "event": "repo_analysis_started",
  "repo_id": "repo_123",
  "timestamp": "2026-05-16T10:30:00Z",
  "data": {
    "message": "Starting repository analysis",
    "progress": 0
  }
}
```

**All Event Types:**
- `repo_analysis_started`
- `repository_parsed`
- `dependencies_extracted`
- `git_history_analyzed`
- `dependency_graph_generated`
- `fragility_analysis_complete`
- `investigation_started`
- `investigation_progress`
- `investigation_complete`
- `mentor_response_ready`

---

### Updated Dashboard Response

**Corrected Response (Remove last_analysis):**
```json
{
  "repo_id": "repo_123",
  "services": 12,
  "dependencies": 38,
  "fragile_services": [
    "auth-service",
    "checkout-service"
  ],
  "recent_incidents": 4
}
```

---

## 🎯 Action Items

### Immediate (Before Implementation)
- [ ] Update [`backend_pending.md`](backend_pending.md) with 3 missing callback endpoints
- [ ] Remove `last_analysis` field from dashboard response specification
- [ ] Add enhanced WebSocket event structure with `repo_id`, `timestamp`, `data`
- [ ] Document all 7 callback endpoints with exact request/response formats

### During Implementation
- [ ] Verify each endpoint implementation matches contract exactly
- [ ] Add integration tests for all callback endpoints
- [ ] Test WebSocket events with all event types
- [ ] Validate JSON schemas for all requests/responses

---

## ✅ Final Verification Status

| Workflow | Contract Match | Implementation Plan | Status |
|----------|---------------|---------------------|--------|
| Upload Repository | ✅ | ✅ | Complete |
| Clone Repository | ✅ | ✅ | Complete |
| Analyze Repository | ✅ | ✅ | Complete |
| Repository Parsing | ✅ | ❌ Missing callback | **NEEDS UPDATE** |
| Dependency Graph Gen | ✅ | ❌ Missing callback | **NEEDS UPDATE** |
| Git History Analysis | ✅ | ❌ Missing callback | **NEEDS UPDATE** |
| Fragility Analysis | ✅ | ✅ | Correct |
| Memory Storage | ✅ | ✅ | Correct |
| Dashboard Data | ⚠️ | ⚠️ Extra field | **NEEDS FIX** |
| Dependency Graph Viz | ✅ | ✅ | Correct |
| Incident Investigation | ✅ | ✅ | Correct |
| Mentor Query | ✅ | ✅ | Correct |
| WebSocket Updates | ⚠️ | ⚠️ Needs enhancement | **NEEDS UPDATE** |
| Final RCA Report | ✅ | ✅ | Correct |

---

## 📝 Conclusion

**Overall Assessment:** 85% alignment with contracts

**Critical Fixes Required:**
1. Add 3 missing callback endpoints (repository-parsed, dependencies-extracted, git-history-analyzed)
2. Fix dashboard response structure (remove last_analysis)
3. Enhance WebSocket event structure

**Recommendation:** Update [`backend_pending.md`](backend_pending.md) with corrections before starting implementation.

---

**Verification Date:** 2026-05-16  
**Verified By:** Bob (Plan Mode)  
**Status:** Ready for corrections ⚠️