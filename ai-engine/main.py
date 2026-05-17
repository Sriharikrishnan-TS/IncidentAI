"""Entrypoint for IncidentOS AI Engine."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.workflow import execute_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IncidentOS AI Engine",
    description="AI-powered repository analysis and incident detection system",
    version="1.0.0"
)


class AnalyzeRepoRequest(BaseModel):
    """Request model for repository analysis."""
    
    repo_id: str = Field(..., description="Unique identifier for the repository")
    repo_path: str = Field(..., description="Local filesystem path to the repository")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_id": "example-repo-123",
                "repo_path": "/path/to/repository"
            }
        }


class AnalyzeRepoResponse(BaseModel):
    """Response model for repository analysis."""
    
    repo_id: str
    status: str
    parsed_repo: dict[str, Any] | None = None
    dependency_graph: dict[str, Any] | None = None
    fragility_scores: dict[str, Any] | None = None
    incidents: list[dict[str, Any]] | None = None
    mentor_context: dict[str, Any] | None = None
    logs: list[dict[str, Any]]
    error: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/analyze-repo", response_model=AnalyzeRepoResponse)
def analyze_repo(request: AnalyzeRepoRequest) -> dict[str, Any]:
    """Analyze a repository using the LangGraph orchestration pipeline.
    
    This endpoint triggers the complete analysis workflow:
    1. Repository parsing
    2. Dependency analysis
    3. Fragility scoring
    4. Incident detection
    5. Mentor guidance generation
    
    Args:
        request: Repository analysis request with repo_id and repo_path
        
    Returns:
        Complete analysis results including all agent outputs
        
    Raises:
        HTTPException: If analysis fails
    """
    logger.info(f"Received analysis request for repo_id={request.repo_id}")
    
    try:
        # Execute the orchestration workflow
        result = execute_workflow(
            repo_id=request.repo_id,
            repo_path=request.repo_path
        )
        
        logger.info(f"Analysis completed for repo_id={request.repo_id} with status={result.get('status')}")
        
        return result
        
    except Exception as e:
        error_msg = f"Repository analysis failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/workflow/visualization")
def get_workflow_visualization() -> dict[str, str]:
    """Get a visual representation of the orchestration workflow.
    
    Returns:
        Workflow structure and flow diagram
    """
    from graph.workflow import get_workflow_visualization
    
    return {
        "workflow": get_workflow_visualization()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
