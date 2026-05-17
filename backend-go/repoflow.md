first look at the context from other readme files and proceed
Integration update 😭🔥

Merged frontend + backend into an `integration-test` branch and tested full-stack integration locally.

What was done:

* connected frontend to real Go backend
* fixed CORS issues
* aligned frontend routes with backend contracts
* validated dashboard API flow
* validated dependency graph API flow
* fragility endpoint connected to backend queue flow
* fixed multiple frontend/backend schema mismatches during integration
* backend stub graph rendering working now

Current status:
✅ dashboard working with backend
✅ dependency graph rendering
✅ frontend ↔ backend communication working
✅ backend server + websocket setup working
✅ integration branch pushed

Known temporary hacks:

* `demo_repo` currently hardcoded
* fragility still returns temporary fallback data until actual AI output endpoint exists
* some backend responses still need schema cleanup (`recent_incidents`, fragility scores etc.)

Next major task:
upload repo → return repo_id → use that repo_id globally across dashboard/graph/fragility flow.
#BOBTHANPOOLEY