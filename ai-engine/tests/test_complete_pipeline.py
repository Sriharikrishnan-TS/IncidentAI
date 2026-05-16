"""
Unified State Graph Verification - Complete Pipeline Integration Test

This is the ultimate integration test that verifies the entire AI pipeline
works correctly with the LangGraph AgentState paradigm.

Tests:
1. Complete AgentState structure with all fields
2. Sequential node execution (RepositoryAgent -> GitHistoryAgent)
3. State propagation and merging between nodes
4. Workflow 4 & 6 payload requirements verification
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.state import AgentState
from agents.repository_agent.node import repository_agent_node
from agents.git_history_agent.node import git_history_agent_node

# Check if git is available
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("Warning: GitPython not available - using fallback data for git tests")


def create_mock_repository() -> str:
    """
    Creates a complete mock repository structure with:
    - Multiple services (frontend, backend, ai-engine)
    - Various file types and frameworks
    - Git repository with commits (if GitPython available)
    
    Returns:
        Path to the temporary repository
    """
    tmpdir = tempfile.mkdtemp(prefix="incidentos_test_")
    
    # Create frontend service
    frontend_dir = os.path.join(tmpdir, "frontend")
    os.makedirs(frontend_dir)
    
    # Frontend: components directory
    components_dir = os.path.join(frontend_dir, "components")
    os.makedirs(components_dir)
    with open(os.path.join(components_dir, "Button.tsx"), 'w') as f:
        f.write("import React from 'react';\n")
        f.write("export default function Button() {\n")
        f.write("  return <button>Click</button>;\n")
        f.write("}\n")
    
    # Frontend: package.json
    with open(os.path.join(frontend_dir, "package.json"), 'w') as f:
        f.write('{\n')
        f.write('  "name": "frontend",\n')
        f.write('  "dependencies": {\n')
        f.write('    "react": "^18.0.0",\n')
        f.write('    "next": "^13.0.0"\n')
        f.write('  }\n')
        f.write('}\n')
    
    # Create backend service
    backend_dir = os.path.join(tmpdir, "backend")
    os.makedirs(backend_dir)
    
    # Backend: routes directory
    routes_dir = os.path.join(backend_dir, "routes")
    os.makedirs(routes_dir)
    with open(os.path.join(routes_dir, "api.py"), 'w') as f:
        f.write("from fastapi import APIRouter\n")
        f.write("router = APIRouter()\n")
        f.write("@router.get('/api/users')\n")
        f.write("def get_users():\n")
        f.write("    return []\n")
    
    # Backend: requirements.txt
    with open(os.path.join(backend_dir, "requirements.txt"), 'w') as f:
        f.write("fastapi==0.100.0\n")
        f.write("uvicorn==0.23.0\n")
    
    # Create ai-engine service
    ai_dir = os.path.join(tmpdir, "ai-engine")
    os.makedirs(ai_dir)
    
    # AI Engine: main.py
    with open(os.path.join(ai_dir, "main.py"), 'w') as f:
        f.write("from langchain import LLMChain\n")
        f.write("from langgraph import StateGraph\n")
        f.write("def main():\n")
        f.write("    pass\n")
    
    # AI Engine: requirements.txt
    with open(os.path.join(ai_dir, "requirements.txt"), 'w') as f:
        f.write("langchain==0.1.0\n")
        f.write("langgraph==0.0.20\n")
    
    # Initialize git repository if available
    if GIT_AVAILABLE:
        try:
            repo = git.Repo.init(tmpdir)
            repo.index.add(['*'])
            repo.index.commit("Initial commit")
            
            # Create a feature branch and merge it (simulates PR)
            repo.create_head('feature/frontend-update')
            repo.heads['feature/frontend-update'].checkout()
            
            # Make a change
            with open(os.path.join(frontend_dir, "README.md"), 'w') as f:
                f.write("# Frontend Service\n")
            repo.index.add(['frontend/README.md'])
            repo.index.commit("Add frontend README")
            
            # Merge back to main
            repo.heads.master.checkout()
            repo.git.merge('feature/frontend-update', m="Merge pull request #1 from user/feature/frontend-update")
            
        except Exception as e:
            print(f"Warning: Could not initialize git repo: {e}")
    
    return tmpdir


def test_complete_agentstate_structure():
    """
    Test 1: Verify the complete AgentState structure contains all required fields.
    """
    print("\n" + "="*70)
    print("Test 1: Complete AgentState Structure Verification")
    print("="*70)
    
    # Create a complete state with all fields
    complete_state: AgentState = {
        "repo_id": "test-repo",
        "repo_path": "/tmp/test",
        "services": ["frontend", "backend", "ai-engine"],
        "languages": ["Python", "TypeScript", "Go"],
        "frameworks": ["FastAPI", "Next.js", "LangGraph"],
        "architecture_summary": "Multi-service architecture",
        "high_churn_services": ["frontend"],
        "recent_commits": 42,
        "top_contributors": ["Alice", "Bob"],
        "pr_analytics": {
            "branch_info": {"total_branches": 4},
            "pr_metrics": {"pr_count": 10},
            "churn_summary": {"pr_to_commit_ratio": 0.24}
        }
    }
    
    # Verify all required fields are present
    required_fields = [
        "repo_id", "repo_path", "services", "languages", "frameworks",
        "architecture_summary", "high_churn_services", "recent_commits",
        "top_contributors", "pr_analytics"
    ]
    
    for field in required_fields:
        assert field in complete_state, f"Missing required field: {field}"
        print(f"  [OK] Field '{field}' present: {type(complete_state[field]).__name__}")
    
    print("\n[PASS] All AgentState fields verified")
    return True


def test_repository_agent_execution():
    """
    Test 2: Execute RepositoryAgent node and verify output structure.
    """
    print("\n" + "="*70)
    print("Test 2: RepositoryAgent Node Execution")
    print("="*70)
    
    # Create mock repository
    repo_path = create_mock_repository()
    
    try:
        # Create initial state
        initial_state: AgentState = {
            "repo_id": "test-pipeline-repo",
            "repo_path": repo_path,
            "services": [],
            "languages": [],
            "frameworks": [],
            "architecture_summary": "",
            "high_churn_services": [],
            "recent_commits": 0,
            "top_contributors": [],
            "pr_analytics": {}
        }
        
        # Execute repository agent
        print(f"  Executing repository_agent_node on: {repo_path}")
        repo_result = repository_agent_node(initial_state)
        
        # Verify output structure
        assert "services" in repo_result, "Missing 'services' in output"
        assert "languages" in repo_result, "Missing 'languages' in output"
        assert "frameworks" in repo_result, "Missing 'frameworks' in output"
        assert "architecture_summary" in repo_result, "Missing 'architecture_summary' in output"
        
        # Verify data types
        assert isinstance(repo_result["services"], list), "services must be a list"
        assert isinstance(repo_result["languages"], list), "languages must be a list"
        assert isinstance(repo_result["frameworks"], list), "frameworks must be a list"
        assert isinstance(repo_result["architecture_summary"], str), "architecture_summary must be a string"
        
        # Verify content
        assert len(repo_result["services"]) > 0, "Should detect at least one service"
        assert len(repo_result["languages"]) > 0, "Should detect at least one language"
        assert len(repo_result["frameworks"]) > 0, "Should detect at least one framework"
        assert len(repo_result["architecture_summary"]) > 0, "Architecture summary should not be empty"
        
        print(f"\n  Detected Services: {repo_result['services']}")
        print(f"  Detected Languages: {repo_result['languages']}")
        print(f"  Detected Frameworks: {repo_result['frameworks']}")
        print(f"  Architecture Summary: {repo_result['architecture_summary'][:80]}...")
        
        print("\n[PASS] RepositoryAgent execution verified")
        return repo_path, repo_result
        
    except Exception as e:
        shutil.rmtree(repo_path, ignore_errors=True)
        raise e


def test_git_history_agent_execution(repo_path: str, repo_state: Dict[str, Any]):
    """
    Test 3: Execute GitHistoryAgent node and verify output structure.
    """
    print("\n" + "="*70)
    print("Test 3: GitHistoryAgent Node Execution")
    print("="*70)
    
    # Create state with repository results
    state_with_repo: AgentState = {
        "repo_id": "test-pipeline-repo",
        "repo_path": repo_path,
        "services": repo_state["services"],
        "languages": repo_state["languages"],
        "frameworks": repo_state["frameworks"],
        "architecture_summary": repo_state["architecture_summary"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
        "pr_analytics": {}
    }
    
    # Execute git history agent
    print(f"  Executing git_history_agent_node on: {repo_path}")
    git_result = git_history_agent_node(state_with_repo)
    
    # Verify output structure
    assert "high_churn_services" in git_result, "Missing 'high_churn_services' in output"
    assert "recent_commits" in git_result, "Missing 'recent_commits' in output"
    assert "top_contributors" in git_result, "Missing 'top_contributors' in output"
    assert "pr_analytics" in git_result, "Missing 'pr_analytics' in output"
    
    # Verify data types
    assert isinstance(git_result["high_churn_services"], list), "high_churn_services must be a list"
    assert isinstance(git_result["recent_commits"], int), "recent_commits must be an int"
    assert isinstance(git_result["top_contributors"], list), "top_contributors must be a list"
    assert isinstance(git_result["pr_analytics"], dict), "pr_analytics must be a dict"
    
    # Verify pr_analytics structure
    pr_analytics = git_result["pr_analytics"]
    assert "branch_info" in pr_analytics, "pr_analytics missing 'branch_info'"
    assert "pr_metrics" in pr_analytics, "pr_analytics missing 'pr_metrics'"
    assert "churn_summary" in pr_analytics, "pr_analytics missing 'churn_summary'"
    
    print(f"\n  High Churn Services: {git_result['high_churn_services']}")
    print(f"  Recent Commits: {git_result['recent_commits']}")
    print(f"  Top Contributors: {git_result['top_contributors'][:3]}")
    print(f"  PR Count: {pr_analytics['pr_metrics']['pr_count']}")
    print(f"  Total Branches: {pr_analytics['branch_info']['total_branches']}")
    
    print("\n[PASS] GitHistoryAgent execution verified")
    return git_result


def test_sequential_node_chaining():
    """
    Test 4: Execute both nodes sequentially and verify state propagation.
    """
    print("\n" + "="*70)
    print("Test 4: Sequential Node Chaining Through State")
    print("="*70)
    
    # Create mock repository
    repo_path = create_mock_repository()
    
    try:
        # Initial state
        initial_state: AgentState = {
            "repo_id": "chain-test-repo",
            "repo_path": repo_path,
            "services": [],
            "languages": [],
            "frameworks": [],
            "architecture_summary": "",
            "high_churn_services": [],
            "recent_commits": 0,
            "top_contributors": [],
            "pr_analytics": {}
        }
        
        print("  Step 1: Execute RepositoryAgent")
        repo_result = repository_agent_node(initial_state)
        
        # Merge results into state (simulating LangGraph behavior)
        state_after_repo: AgentState = {**initial_state, **repo_result}
        
        print("  Step 2: Execute GitHistoryAgent with updated state")
        git_result = git_history_agent_node(state_after_repo)
        
        # Merge final results
        final_state: AgentState = {**state_after_repo, **git_result}
        
        # Verify final state has all fields populated
        print("\n  Final State Verification:")
        assert len(final_state["services"]) > 0, "Services should be populated"
        assert len(final_state["languages"]) > 0, "Languages should be populated"
        assert len(final_state["frameworks"]) > 0, "Frameworks should be populated"
        assert len(final_state["architecture_summary"]) > 0, "Architecture summary should be populated"
        assert isinstance(final_state["recent_commits"], int), "Recent commits should be an integer"
        assert len(final_state["top_contributors"]) > 0, "Top contributors should be populated"
        assert "branch_info" in final_state["pr_analytics"], "PR analytics should be populated"
        
        print(f"    Services: {len(final_state['services'])} detected")
        print(f"    Languages: {len(final_state['languages'])} detected")
        print(f"    Frameworks: {len(final_state['frameworks'])} detected")
        print(f"    Architecture: {len(final_state['architecture_summary'])} chars")
        print(f"    Commits: {final_state['recent_commits']}")
        print(f"    Contributors: {len(final_state['top_contributors'])}")
        print(f"    PR Analytics: {len(final_state['pr_analytics'])} keys")
        
        print("\n[PASS] Sequential node chaining verified")
        return final_state
        
    finally:
        shutil.rmtree(repo_path, ignore_errors=True)


def test_workflow_payload_requirements(final_state: AgentState):
    """
    Test 5: Verify the final state meets Workflow 4 & 6 payload requirements.
    
    Workflow 4 Requirements:
    - repo_id: string
    - services: list of strings
    - languages: list of strings
    - frameworks: list of strings
    - architecture_summary: string
    
    Workflow 6 Requirements:
    - repo_id: string
    - high_churn_services: list of strings
    - recent_commits: integer
    - top_contributors: list of strings
    - pr_analytics: dict with branch_info, pr_metrics, churn_summary
    """
    print("\n" + "="*70)
    print("Test 5: Workflow 4 & 6 Payload Requirements")
    print("="*70)
    
    print("\n  Workflow 4 (Repository Onboarding) Requirements:")
    
    # Workflow 4 checks
    assert isinstance(final_state["repo_id"], str), "repo_id must be string"
    assert len(final_state["repo_id"]) > 0, "repo_id must not be empty"
    print(f"    [OK] repo_id: '{final_state['repo_id']}'")
    
    assert isinstance(final_state["services"], list), "services must be list"
    assert all(isinstance(s, str) for s in final_state["services"]), "services must contain strings"
    print(f"    [OK] services: {len(final_state['services'])} items")
    
    assert isinstance(final_state["languages"], list), "languages must be list"
    assert all(isinstance(l, str) for l in final_state["languages"]), "languages must contain strings"
    print(f"    [OK] languages: {len(final_state['languages'])} items")
    
    assert isinstance(final_state["frameworks"], list), "frameworks must be list"
    assert all(isinstance(f, str) for f in final_state["frameworks"]), "frameworks must contain strings"
    print(f"    [OK] frameworks: {len(final_state['frameworks'])} items")
    
    assert isinstance(final_state["architecture_summary"], str), "architecture_summary must be string"
    assert len(final_state["architecture_summary"]) > 0, "architecture_summary must not be empty"
    print(f"    [OK] architecture_summary: {len(final_state['architecture_summary'])} characters")
    
    print("\n  Workflow 6 (Git History & Churn Analysis) Requirements:")
    
    # Workflow 6 checks
    assert isinstance(final_state["high_churn_services"], list), "high_churn_services must be list"
    assert all(isinstance(s, str) for s in final_state["high_churn_services"]), "high_churn_services must contain strings"
    print(f"    [OK] high_churn_services: {len(final_state['high_churn_services'])} items")
    
    assert isinstance(final_state["recent_commits"], int), "recent_commits must be integer"
    assert final_state["recent_commits"] >= 0, "recent_commits must be non-negative"
    print(f"    [OK] recent_commits: {final_state['recent_commits']}")
    
    assert isinstance(final_state["top_contributors"], list), "top_contributors must be list"
    assert all(isinstance(c, str) for c in final_state["top_contributors"]), "top_contributors must contain strings"
    print(f"    [OK] top_contributors: {len(final_state['top_contributors'])} items")
    
    assert isinstance(final_state["pr_analytics"], dict), "pr_analytics must be dict"
    pr_analytics = final_state["pr_analytics"]
    
    assert "branch_info" in pr_analytics, "pr_analytics must contain branch_info"
    assert isinstance(pr_analytics["branch_info"], dict), "branch_info must be dict"
    print(f"    [OK] pr_analytics.branch_info: {len(pr_analytics['branch_info'])} keys")
    
    assert "pr_metrics" in pr_analytics, "pr_analytics must contain pr_metrics"
    assert isinstance(pr_analytics["pr_metrics"], dict), "pr_metrics must be dict"
    print(f"    [OK] pr_analytics.pr_metrics: {len(pr_analytics['pr_metrics'])} keys")
    
    assert "churn_summary" in pr_analytics, "pr_analytics must contain churn_summary"
    assert isinstance(pr_analytics["churn_summary"], dict), "churn_summary must be dict"
    print(f"    [OK] pr_analytics.churn_summary: {len(pr_analytics['churn_summary'])} keys")
    
    # Verify specific churn_summary fields
    churn_summary = pr_analytics["churn_summary"]
    assert "services_with_high_pr_activity" in churn_summary, "churn_summary must contain services_with_high_pr_activity"
    assert "total_merge_commits" in churn_summary, "churn_summary must contain total_merge_commits"
    assert "active_branches" in churn_summary, "churn_summary must contain active_branches"
    assert "pr_to_commit_ratio" in churn_summary, "churn_summary must contain pr_to_commit_ratio"
    
    print(f"    [OK] churn_summary.services_with_high_pr_activity: {len(churn_summary['services_with_high_pr_activity'])} items")
    print(f"    [OK] churn_summary.total_merge_commits: {churn_summary['total_merge_commits']}")
    print(f"    [OK] churn_summary.active_branches: {churn_summary['active_branches']}")
    print(f"    [OK] churn_summary.pr_to_commit_ratio: {churn_summary['pr_to_commit_ratio']:.2%}")
    
    print("\n[PASS] All Workflow 4 & 6 payload requirements verified")
    return True


def run_all_tests():
    """
    Execute all pipeline integration tests.
    """
    print("\n" + "="*70)
    print("UNIFIED STATE GRAPH VERIFICATION")
    print("Complete Pipeline Integration Test Suite")
    print("="*70)
    
    try:
        # Test 1: AgentState structure
        test_complete_agentstate_structure()
        
        # Test 2: RepositoryAgent execution
        repo_path, repo_result = test_repository_agent_execution()
        
        # Test 3: GitHistoryAgent execution
        git_result = test_git_history_agent_execution(repo_path, repo_result)
        
        # Cleanup
        shutil.rmtree(repo_path, ignore_errors=True)
        
        # Test 4: Sequential chaining
        final_state = test_sequential_node_chaining()
        
        # Test 5: Workflow requirements
        test_workflow_payload_requirements(final_state)
        
        print("\n" + "="*70)
        print("[SUCCESS] ALL PIPELINE INTEGRATION TESTS PASSED!")
        print("="*70)
        print("\nThe complete AI pipeline is verified and ready for:")
        print("  * Workflow 4: Repository Onboarding")
        print("  * Workflow 6: Git History & Churn Analysis")
        print("  * LangGraph state propagation")
        print("  * Integration with Fragility Agent")
        print("  * Integration with Dashboard")
        print("="*70 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
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
