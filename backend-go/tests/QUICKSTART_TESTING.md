# IncidentOS Backend - Quick Start Testing Guide

## 🚀 Quick Start

### 1. Start Required Services

```bash
# Start Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Start ChromaDB
docker run -d \
  --name chromadb \
  -p 8001:8000 \
  chromadb/chroma:latest
```

### 2. Set Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Or set manually
export PORT=8080
export AI_ENGINE_URL=http://localhost:8001
export REPOS_DIR=./repos
export CALLBACK_API_KEY=test-callback-key-12345
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password
export CHROMADB_URL=http://localhost:8001
```

### 3. Start Backend Server

```bash
cd backend-go
go run main.go
```

Expected output:
```
[Main] Starting IncidentOS Backend
[Main] Port: 8080
[Main] AI Engine URL: http://localhost:8001
[Main] Repos Directory: ./repos
[Main] Neo4j URI: bolt://localhost:7687
[Main] ChromaDB URL: http://localhost:8001
[Main] CloneService initialized
[Main] JobQueue initialized
[Main] JobQueue worker started
[Main] WebSocket Hub initialized
[Main] WebSocket Hub started
[Main] Neo4j client initialized successfully
[Main] ChromaDB client connected successfully
[Main] Investigation Manager initialized
[Main] Gateway initialized
[Main] Routes registered
[Main] WebSocket endpoint registered at /ws
[Main] HTTP server listening on :8080
```

### 4. Run Integration Tests

```bash
# In a new terminal
cd backend-go
./test_integration.sh
```

## 📋 Test Categories

The integration test suite covers:

1. **Health Check** - Server availability
2. **Repository Upload** - GitHub URL validation and cloning
3. **Repository Analysis** - Job queuing for AI analysis
4. **Fragility Computation** - Fragility score calculation
5. **Investigation Lifecycle** - Start, track, and list investigations
6. **Dashboard Data** - Real-time metrics retrieval
7. **Dependency Graph** - Graph data from Neo4j
8. **Mentor Queries** - Knowledge base queries
9. **Callback Authentication** - API key validation
10. **Concurrent Operations** - Multiple simultaneous requests
11. **Load Testing** - Multiple repository handling
12. **Error Handling** - Invalid input validation
13. **WebSocket Streaming** - Real-time event delivery

## 🧪 Individual Test Examples

### Test Health Check
```bash
curl http://localhost:8080/health
```

### Test Repository Upload
```bash
curl -X POST http://localhost:8080/upload-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/torvalds/linux"}'
```

### Test Investigation Start
```bash
curl -X POST http://localhost:8080/start-investigation \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "YOUR_REPO_ID",
    "incident": "API timeout in checkout service"
  }'
```

### Test WebSocket Connection
```bash
# Using websocat (install: cargo install websocat)
websocat ws://localhost:8080/ws

# Or open test_websocket.html in browser
```

### Test Callback Endpoint
```bash
curl -X POST http://localhost:8080/callback/fragility-complete \
  -H "Content-Type: application/json" \
  -H "X-Callback-API-Key: test-callback-key-12345" \
  -d '{
    "repo_id": "test123",
    "fragility_scores": [
      {
        "service": "auth-service",
        "score": 8.5,
        "reasons": ["high churn", "high centrality"]
      }
    ]
  }'
```

## 🔍 Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8080

# Kill existing process
kill -9 $(lsof -t -i:8080)
```

### Neo4j connection failed
```bash
# Check Neo4j status
docker ps | grep neo4j

# View Neo4j logs
docker logs neo4j

# Restart Neo4j
docker restart neo4j
```

### ChromaDB not accessible
```bash
# Check ChromaDB status
docker ps | grep chroma

# Test ChromaDB health
curl http://localhost:8001/api/v1/heartbeat

# Restart ChromaDB
docker restart chromadb
```

### Tests failing
```bash
# Check server logs
# Look for error messages in terminal running go run main.go

# Verify environment variables
env | grep -E 'PORT|NEO4J|CHROMA|CALLBACK'

# Check database connectivity
curl http://localhost:7474  # Neo4j browser
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB
```

## 📊 Expected Test Results

```
========================================
Test Summary
========================================

Total Tests:  30
Passed:       30
Failed:       0

✓ ALL TESTS PASSED!
Phase 6 Integration Testing: COMPLETE
```

## 🎯 Performance Benchmarks

| Metric | Expected |
|--------|----------|
| API Response Time | < 200ms |
| WebSocket Latency | < 100ms |
| Concurrent Connections | 100+ |
| Repository Upload | < 5s |

## 📚 Additional Resources

- **Full Documentation:** `PHASE6_INTEGRATION.md`
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Security Guide:** `SECURITY.md`
- **API Contracts:** `contracts.md`

## 🆘 Getting Help

If tests fail or you encounter issues:

1. Check server logs for error messages
2. Verify all environment variables are set
3. Ensure Neo4j and ChromaDB are running
4. Review `PHASE6_INTEGRATION.md` troubleshooting section
5. Check individual test scripts:
   - `test_neo4j.sh` - Neo4j connectivity
   - `test_chromadb.sh` - ChromaDB connectivity
   - `test_callbacks.sh` - Callback endpoints
   - `test_integration.sh` - Full integration

## ✅ Success Criteria

Your setup is working correctly if:

- ✅ Server starts without errors
- ✅ Health check returns `{"status":"ok"}`
- ✅ Neo4j connection successful
- ✅ ChromaDB connection successful
- ✅ All integration tests pass
- ✅ WebSocket connections work
- ✅ Callback authentication works

---

**Ready to test?** Run `./test_integration.sh` and watch the magic happen! 🚀