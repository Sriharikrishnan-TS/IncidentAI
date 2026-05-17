"""
Test suite for PR and branch churn analytics in GitHistoryAgent.

Tests the branch tracking, PR analysis, and churn pattern detection features.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.state import AgentState

# Check if GitPython is available
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("Warning: GitPython not available - some tests will be skipped")


def test_pr_analytics_fallback():
    """Test that fallback data includes pr_analytics."""
    from agents.git_history_agent.node import _get_fallback_data
    
    fallback = _get_fallback_data()
    
    assert "pr_analytics" in fallback, "Fallback data should include pr_analytics"
    assert "branch_info" in fallback["pr_analytics"], "pr_analytics should include branch_info"
    assert "pr_metrics" in fallback["pr_analytics"], "pr_analytics should include pr_metrics"
    assert "churn_summary" in fallback["pr_analytics"], "pr_analytics should include churn_summary"
    
    # Verify branch_info structure
    branch_info = fallback["pr_analytics"]["branch_info"]
    assert "local_branches" in branch_info
    assert "remote_branches" in branch_info
    assert "active_branches" in branch_info
    assert "total_branches" in branch_info
    
    # Verify pr_metrics structure
    pr_metrics = fallback["pr_analytics"]["pr_metrics"]
    assert "total_merge_commits" in pr_metrics
    assert "pr_count" in pr_metrics
    assert "branch_merges" in pr_metrics
    assert "service_pr_activity" in pr_metrics
    assert "services_with_high_pr_activity" in pr_metrics
    
    # Verify churn_summary structure
    churn_summary = fallback["pr_analytics"]["churn_summary"]
    assert "services_with_high_pr_activity" in churn_summary
    assert "total_merge_commits" in churn_summary
    assert "active_branches" in churn_summary
    assert "pr_to_commit_ratio" in churn_summary
    
    print("[PASS] PR analytics fallback data structure test passed")


def test_extract_service_from_branch():
    """Test service extraction from branch names."""
    from agents.git_history_agent.node import _extract_service_from_branch
    
    services = ["frontend", "backend-go", "ai-engine"]
    
    # Test various branch naming patterns
    assert _extract_service_from_branch("user/frontend-feature", services) == "frontend"
    assert _extract_service_from_branch("backend-go/fix-bug", services) == "backend-go"
    assert _extract_service_from_branch("feature/ai-engine-update", services) == "ai-engine"
    assert _extract_service_from_branch("hotfix/database-issue", services) == ""
    assert _extract_service_from_branch("main", services) == ""
    
    print("[PASS] Service extraction from branch names test passed")


def test_git_history_agent_with_pr_analytics():
    """Test the full git history agent node with PR analytics."""
    if not GIT_AVAILABLE:
        print("[SKIP] GitPython not available - skipping git history agent test")
        return
    
    from agents.git_history_agent.node import git_history_agent_node
    
    # Use the actual IncidentOS repository
    repo_path = str(Path(__file__).parent.parent.parent)
    
    # Create initial state
    state: AgentState = {
        "repo_id": "test-repo",
        "repo_path": repo_path,
        "services": ["frontend", "backend-go", "ai-engine"],
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "Gin", "Next.js"],
        "architecture_summary": "Multi-service architecture",
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
        "pr_analytics": {}
    }
    
    # Run the git history agent
    result = git_history_agent_node(state)
    
    # Verify results
    assert "pr_analytics" in result, "Result should contain pr_analytics"
    
    pr_analytics = result["pr_analytics"]
    assert "branch_info" in pr_analytics, "pr_analytics should include branch_info"
    assert "pr_metrics" in pr_analytics, "pr_analytics should include pr_metrics"
    assert "churn_summary" in pr_analytics, "pr_analytics should include churn_summary"
    
    # Verify branch info
    branch_info = pr_analytics["branch_info"]
    assert isinstance(branch_info["local_branches"], list)
    assert isinstance(branch_info["remote_branches"], list)
    assert isinstance(branch_info["active_branches"], list)
    assert isinstance(branch_info["total_branches"], int)
    
    # Verify PR metrics
    pr_metrics = pr_analytics["pr_metrics"]
    assert isinstance(pr_metrics["total_merge_commits"], int)
    assert isinstance(pr_metrics["pr_count"], int)
    assert isinstance(pr_metrics["branch_merges"], list)
    assert isinstance(pr_metrics["service_pr_activity"], list)
    
    # Verify churn summary
    churn_summary = pr_analytics["churn_summary"]
    assert isinstance(churn_summary["services_with_high_pr_activity"], list)
    assert isinstance(churn_summary["total_merge_commits"], int)
    assert isinstance(churn_summary["active_branches"], int)
    assert isinstance(churn_summary["pr_to_commit_ratio"], (int, float))
    
    print("[PASS] Full git history agent with PR analytics test passed")
    print(f"  Branches: {branch_info['total_branches']} total, {len(branch_info['active_branches'])} active")
    print(f"  PRs: {pr_metrics['pr_count']} analyzed, {pr_metrics['total_merge_commits']} merge commits")
    print(f"  High PR activity services: {churn_summary['services_with_high_pr_activity']}")
    print(f"  PR to commit ratio: {churn_summary['pr_to_commit_ratio']:.2f}")


def test_pr_analytics_for_fragility_agent():
    """Test that PR analytics provides useful data for fragility scoring."""
    if not GIT_AVAILABLE:
        print("[SKIP] GitPython not available - skipping fragility integration test")
        return
    
    from agents.git_history_agent.node import git_history_agent_node
    
    repo_path = str(Path(__file__).parent.parent.parent)
    
    state: AgentState = {
        "repo_id": "fragility-test",
        "repo_path": repo_path,
        "services": ["frontend", "backend-go", "ai-engine"],
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "Gin", "Next.js"],
        "architecture_summary": "Multi-service architecture",
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
        "pr_analytics": {}
    }
    
    result = git_history_agent_node(state)
    pr_analytics = result["pr_analytics"]
    
    # Verify fragility-relevant metrics are present
    churn_summary = pr_analytics["churn_summary"]
    
    # Services with high PR activity indicate areas of frequent change
    assert "services_with_high_pr_activity" in churn_summary
    high_activity_services = churn_summary["services_with_high_pr_activity"]
    
    # High PR to commit ratio might indicate instability
    pr_ratio = churn_summary["pr_to_commit_ratio"]
    assert pr_ratio >= 0 and pr_ratio <= 1, "PR ratio should be between 0 and 1"
    
    # Many active branches might indicate parallel development and potential conflicts
    active_branch_count = churn_summary["active_branches"]
    assert active_branch_count >= 0
    
    print("[PASS] PR analytics for fragility agent test passed")
    print(f"  Fragility indicators:")
    print(f"    - High activity services: {high_activity_services}")
    print(f"    - PR/commit ratio: {pr_ratio:.2f} {'(high churn)' if pr_ratio > 0.3 else '(stable)'}")
    print(f"    - Active branches: {active_branch_count} {'(many)' if active_branch_count > 5 else '(few)'}")


def run_all_tests():
    """Run all PR analytics tests."""
    print("\n" + "="*70)
    print("Running PR and Branch Churn Analytics Tests")
    print("="*70 + "\n")
    
    try:
        test_pr_analytics_fallback()
        test_extract_service_from_branch()
        test_git_history_agent_with_pr_analytics()
        test_pr_analytics_for_fragility_agent()
        
        print("\n" + "="*70)
        print("[SUCCESS] All PR analytics tests passed!")
        print("="*70 + "\n")
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
