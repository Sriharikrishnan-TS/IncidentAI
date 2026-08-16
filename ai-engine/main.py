"""Entrypoint for IncidentOS AI Engine."""

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.workflow import execute_workflow
from agents.incident_agent.node import detect_incidents
from agents.mentor_agent.node import generate_mentorship

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IncidentOS AI Engine",
    description="AI-powered repository analysis and incident detection system powered by Groq Llama-3.3-70b",
    version="1.0.0"
)


def _resolve_repo_path(repo_id: str, provided_path: str | None = None) -> str:
    """Helper to reliably find the absolute local path of cloned repos."""
    if provided_path and os.path.exists(provided_path):
        return os.path.abspath(provided_path)
    
    candidates = [
        provided_path,
        os.path.abspath(f"../backend-go/repos/{repo_id}"),
        os.path.abspath(f"./repos/{repo_id}"),
        os.path.abspath(f"../repos/{repo_id}"),
    ]
    
    for cand in candidates:
        if cand and os.path.exists(cand):
            logger.info(f"Resolved repo_id={repo_id} to path: {cand}")
            return cand
            
    fallback = os.path.abspath(f"../backend-go/repos/{repo_id}")
    logger.warning(f"Could not locate existing folder for repo_id={repo_id}, defaulting to fallback: {fallback}")
    return fallback


class AnalyzeRepoRequest(BaseModel):
    repo_id: str = Field(..., description="Unique identifier for the repository")
    repo_path: str = Field(..., description="Local filesystem path to the repository")


class ComputeFragilityRequest(BaseModel):
    repo_id: str
    repo_path: str | None = None


class StartInvestigationRequest(BaseModel):
    repo_id: str
    incident: str | None = None
    repo_path: str | None = None


class MentorQueryRequest(BaseModel):
    repo_id: str
    question: str
    repo_path: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/analyze-repo")
def analyze_repo(request: AnalyzeRepoRequest) -> dict[str, Any]:
    """Analyze a repository using the LangGraph orchestration pipeline."""
    logger.info(f"Received analysis request for repo_id={request.repo_id}")
    try:
        resolved_path = _resolve_repo_path(request.repo_id, request.repo_path)
        result = execute_workflow(
            repo_id=request.repo_id,
            repo_path=resolved_path
        )
        logger.info(f"Analysis completed for repo_id={request.repo_id} with status={result.get('status')}")
        return result
    except Exception as e:
        error_msg = f"Repository analysis failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/compute-fragility")
def compute_fragility(request: ComputeFragilityRequest) -> dict[str, Any]:
    """Compute fragility scores endpoint."""
    logger.info(f"Received compute-fragility request for repo_id={request.repo_id}")
    try:
        resolved_path = _resolve_repo_path(request.repo_id, request.repo_path)
        result = execute_workflow(
            repo_id=request.repo_id,
            repo_path=resolved_path
        )
        return {
            "repo_id": request.repo_id,
            "status": "completed",
            "fragility_scores": result.get("fragility_scores", {})
        }
    except Exception as e:
        logger.error(f"Fragility computation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-investigation")
def start_investigation(request: StartInvestigationRequest) -> dict[str, Any]:
    """Start incident investigation endpoint."""
    logger.info(f"Received start-investigation request for repo_id={request.repo_id}")
    try:
        resolved_path = _resolve_repo_path(request.repo_id, request.repo_path)
        result = execute_workflow(
            repo_id=request.repo_id,
            repo_path=resolved_path
        )
        return {
            "repo_id": request.repo_id,
            "status": "completed",
            "incidents": result.get("incidents", []),
            "mentor_context": result.get("mentor_context", {})
        }
    except Exception as e:
        logger.error(f"Investigation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


from agents.mentor_agent.node import generate_mentorship, answer_mentor_question


@app.post("/mentor-query")
def mentor_query(request: MentorQueryRequest) -> dict[str, Any]:
    """Mentor query endpoint powered by Groq Llama-3.3-70b."""
    logger.info(f"Received mentor-query request for repo_id={request.repo_id}")
    try:
        resolved_path = _resolve_repo_path(request.repo_id, request.repo_path)
        answer = answer_mentor_question(
            repo_id=request.repo_id,
            question=request.question,
            repo_path=resolved_path
        )
        return {
            "repo_id": request.repo_id,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"Mentor query failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/visualization")
def get_workflow_visualization() -> dict[str, str]:
    """Get a visual representation of the orchestration workflow."""
    from graph.workflow import get_workflow_visualization
    return {"workflow": get_workflow_visualization()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
