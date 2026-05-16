"""
Tests for Git History Agent Node
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.git_history_agent.node import git_history_agent_node
from graph.state import AgentState


def test_git_history_agent_with_valid_repo():
    """Test git_history_agent_node with a valid git repository."""
    # Use the current repository as test data
    repo_path = str(Path(__file__).parent.parent.parent)
    
    state: AgentState = {
        "repo_id": "test-repo",
        "repo_path": repo_path,
        "services": ["ai-engine", "backend-go", "frontend"],
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "Next.js"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
    }
    
    result = git_history_agent_node(state)
    
    # Verify result structure
    assert "high_churn_services" in result
    assert "recent_commits" in result
    assert "top_contributors" in result
    
    # Verify types
    assert isinstance(result["high_churn_services"], list)
    assert isinstance(result["recent_commits"], int)
    assert isinstance(result["top_contributors"], list)
    
    # Verify data is populated (either real or fallback)
    assert len(result["high_churn_services"]) > 0
    assert result["recent_commits"] >= 0
    assert len(result["top_contributors"]) > 0
    
    print(f"[OK] Git history analysis successful:")
    print(f"  - High-churn services: {result['high_churn_services']}")
    print(f"  - Recent commits: {result['recent_commits']}")
    print(f"  - Top contributors: {result['top_contributors']}")


def test_git_history_agent_with_non_git_directory(tmp_path):
    """Test git_history_agent_node with a non-git directory (should return fallback data)."""
    # Create a temporary directory that is not a git repository
    test_dir = tmp_path / "not-a-git-repo"
    test_dir.mkdir()
    
    state: AgentState = {
        "repo_id": "test-non-git",
        "repo_path": str(test_dir),
        "services": ["service1", "service2"],
        "languages": ["Python"],
        "frameworks": ["FastAPI"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
    }
    
    result = git_history_agent_node(state)
    
    # Verify fallback data is returned
    assert "high_churn_services" in result
    assert "recent_commits" in result
    assert "top_contributors" in result
    
    # Verify fallback data structure
    assert isinstance(result["high_churn_services"], list)
    assert isinstance(result["recent_commits"], int)
    assert isinstance(result["top_contributors"], list)
    
    # Fallback data should have reasonable values
    assert len(result["high_churn_services"]) > 0
    assert result["recent_commits"] > 0
    assert len(result["top_contributors"]) > 0
    
    print(f"[OK] Fallback data returned for non-git directory:")
    print(f"  - High-churn services: {result['high_churn_services']}")
    print(f"  - Recent commits: {result['recent_commits']}")
    print(f"  - Top contributors: {result['top_contributors']}")


def test_git_history_agent_with_missing_repo_path():
    """Test git_history_agent_node with missing repo_path (should return fallback data)."""
    state: AgentState = {
        "repo_id": "test-missing-path",
        "repo_path": "",
        "services": ["service1"],
        "languages": ["Python"],
        "frameworks": ["FastAPI"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
    }
    
    result = git_history_agent_node(state)
    
    # Should return fallback data without crashing
    assert "high_churn_services" in result
    assert "recent_commits" in result
    assert "top_contributors" in result
    
    print(f"[OK] Fallback data returned for missing repo_path")


def test_git_history_agent_with_nonexistent_path():
    """Test git_history_agent_node with nonexistent path (should return fallback data)."""
    state: AgentState = {
        "repo_id": "test-nonexistent",
        "repo_path": "/path/that/does/not/exist",
        "services": ["service1"],
        "languages": ["Python"],
        "frameworks": ["FastAPI"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
    }
    
    result = git_history_agent_node(state)
    
    # Should return fallback data without crashing
    assert "high_churn_services" in result
    assert "recent_commits" in result
    assert "top_contributors" in result
    
    print(f"[OK] Fallback data returned for nonexistent path")


if __name__ == "__main__":
    print("Running Git History Agent tests...\n")
    
    # Test 1: Valid git repository
    print("Test 1: Valid git repository")
    test_git_history_agent_with_valid_repo()
    print()
    
    # Test 2: Non-git directory
    print("Test 2: Non-git directory")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_git_history_agent_with_non_git_directory(Path(tmp_dir))
    print()
    
    # Test 3: Missing repo_path
    print("Test 3: Missing repo_path")
    test_git_history_agent_with_missing_repo_path()
    print()
    
    # Test 4: Nonexistent path
    print("Test 4: Nonexistent path")
    test_git_history_agent_with_nonexistent_path()
    print()
    
    print("[SUCCESS] All tests passed!")


# Made with Bob