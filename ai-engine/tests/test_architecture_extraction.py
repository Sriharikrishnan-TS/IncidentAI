"""
Test suite for architecture extraction functionality in RepositoryAgent.

Tests the semantic architecture classification and summary generation features.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.repository_agent.node import (
    repository_agent_node,
    _classify_service_architecture,
    _generate_architecture_summary,
    _scan_repo_structure
)
from graph.state import AgentState


def test_classify_frontend_service():
    """Test classification of a frontend service with React components."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a frontend-like structure
        frontend_path = os.path.join(tmpdir, "frontend")
        os.makedirs(frontend_path)
        
        # Create components directory
        components_dir = os.path.join(frontend_path, "components")
        os.makedirs(components_dir)
        
        # Create a React component file
        component_file = os.path.join(components_dir, "Button.tsx")
        with open(component_file, 'w') as f:
            f.write("import React from 'react';\n")
            f.write("export default function Button() {\n")
            f.write("  return <button>Click me</button>;\n")
            f.write("}\n")
        
        # Test classification
        arch_role = _classify_service_architecture(frontend_path, "frontend")
        assert arch_role == "FRONTEND_APPLICATION", f"Expected FRONTEND_APPLICATION, got {arch_role}"
        print("[PASS] Frontend service classification test passed")


def test_classify_backend_service():
    """Test classification of a backend service with API routes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a backend-like structure
        backend_path = os.path.join(tmpdir, "backend")
        os.makedirs(backend_path)
        
        # Create routes directory
        routes_dir = os.path.join(backend_path, "routes")
        os.makedirs(routes_dir)
        
        # Create a route file with FastAPI patterns
        route_file = os.path.join(routes_dir, "api.py")
        with open(route_file, 'w') as f:
            f.write("from fastapi import APIRouter\n")
            f.write("router = APIRouter()\n")
            f.write("@app.get('/api/users')\n")
            f.write("def get_users():\n")
            f.write("    return []\n")
        
        # Test classification
        arch_role = _classify_service_architecture(backend_path, "backend")
        assert arch_role in ["REST_API_GATEWAY", "MICROSERVICE_BACKEND"], \
            f"Expected REST_API_GATEWAY or MICROSERVICE_BACKEND, got {arch_role}"
        print("[PASS] Backend service classification test passed")


def test_generate_architecture_summary_single_service():
    """Test architecture summary generation for a single service."""
    service_architectures = {
        "frontend": "FRONTEND_APPLICATION"
    }
    all_services = {"frontend"}
    
    summary = _generate_architecture_summary(service_architectures, all_services)
    
    assert "frontend" in summary.lower(), "Summary should mention frontend service"
    assert "single-service" in summary.lower() or "frontend application" in summary.lower(), \
        "Summary should indicate single-service architecture"
    print(f"[PASS] Single service summary test passed: {summary}")


def test_generate_architecture_summary_multi_service():
    """Test architecture summary generation for multiple services."""
    service_architectures = {
        "frontend": "FRONTEND_APPLICATION",
        "backend-go": "REST_API_GATEWAY",
        "ai-engine": "MICROSERVICE_BACKEND"
    }
    all_services = {"frontend", "backend-go", "ai-engine"}
    
    summary = _generate_architecture_summary(service_architectures, all_services)
    
    assert "multi-service" in summary.lower(), "Summary should indicate multi-service architecture"
    assert "frontend" in summary.lower(), "Summary should mention frontend"
    assert "backend" in summary.lower() or "api" in summary.lower(), \
        "Summary should mention backend services"
    print(f"[PASS] Multi-service summary test passed: {summary}")


def test_repository_agent_with_architecture():
    """Test the full repository agent node with architecture extraction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a multi-service repository structure
        
        # Frontend service
        frontend_path = os.path.join(tmpdir, "frontend")
        os.makedirs(frontend_path)
        components_dir = os.path.join(frontend_path, "components")
        os.makedirs(components_dir)
        with open(os.path.join(components_dir, "App.tsx"), 'w') as f:
            f.write("import React from 'react';\n")
            f.write("export default function App() { return <div>App</div>; }\n")
        
        # Backend service
        backend_path = os.path.join(tmpdir, "backend")
        os.makedirs(backend_path)
        routes_dir = os.path.join(backend_path, "routes")
        os.makedirs(routes_dir)
        with open(os.path.join(routes_dir, "main.go"), 'w') as f:
            f.write("package routes\n")
            f.write("func HandleFunc() {}\n")
        
        # Create initial state
        state: AgentState = {
            "repo_id": "test-repo",
            "repo_path": tmpdir,
            "services": [],
            "languages": [],
            "frameworks": [],
            "architecture_summary": "",
            "high_churn_services": [],
            "recent_commits": 0,
            "top_contributors": [],
            "pr_analytics": {}
        }
        
        # Run the repository agent
        result = repository_agent_node(state)
        
        # Verify results
        assert "services" in result, "Result should contain services"
        assert "languages" in result, "Result should contain languages"
        assert "frameworks" in result, "Result should contain frameworks"
        assert "architecture_summary" in result, "Result should contain architecture_summary"
        
        assert len(result["services"]) > 0, "Should detect at least one service"
        assert result["architecture_summary"], "Architecture summary should not be empty"
        
        print(f"[PASS] Full repository agent test passed")
        print(f"  Services: {result['services']}")
        print(f"  Languages: {result['languages']}")
        print(f"  Architecture: {result['architecture_summary']}")


def test_empty_repository():
    """Test handling of empty repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state: AgentState = {
            "repo_id": "empty-repo",
            "repo_path": tmpdir,
            "services": [],
            "languages": [],
            "frameworks": [],
            "architecture_summary": "",
            "high_churn_services": [],
            "recent_commits": 0,
            "top_contributors": [],
            "pr_analytics": {}
        }
        
        result = repository_agent_node(state)
        
        assert "architecture_summary" in result, "Result should contain architecture_summary"
        assert "no services" in result["architecture_summary"].lower() or \
               "unclassified" in result["architecture_summary"].lower(), \
               "Summary should indicate no services detected"
        print(f"[PASS] Empty repository test passed: {result['architecture_summary']}")


def run_all_tests():
    """Run all architecture extraction tests."""
    print("\n" + "="*60)
    print("Running Architecture Extraction Tests")
    print("="*60 + "\n")
    
    try:
        test_classify_frontend_service()
        test_classify_backend_service()
        test_generate_architecture_summary_single_service()
        test_generate_architecture_summary_multi_service()
        test_repository_agent_with_architecture()
        test_empty_repository()
        
        print("\n" + "="*60)
        print("[SUCCESS] All architecture extraction tests passed!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
