"""
Demonstration script for Git History Agent
Shows the actual git analysis when GitPython is installed.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.git_history_agent.node import git_history_agent_node
from graph.state import AgentState


def demo_git_history_analysis():
    """
    Demonstrates the git history agent with the current repository.
    """
    print("=" * 70)
    print("Git History Agent Demonstration")
    print("=" * 70)
    print()
    
    # Use the current repository as test data
    repo_path = str(Path(__file__).parent.parent.parent)
    
    # Create a sample state with discovered services
    state: AgentState = {
        "repo_id": "incidentos-demo",
        "repo_path": repo_path,
        "services": ["ai-engine", "backend-go", "frontend"],
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "Next.js", "LangGraph"],
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
    }
    
    print(f"Repository Path: {repo_path}")
    print(f"Detected Services: {', '.join(state['services'])}")
    print()
    print("Analyzing git history (last 100 commits)...")
    print("-" * 70)
    
    # Run the git history agent
    result = git_history_agent_node(state)
    
    print()
    print("Analysis Results:")
    print("-" * 70)
    print()
    
    print(f"[COMMITS] Recent Commits Analyzed: {result['recent_commits']}")
    print()
    
    print(f"[HIGH-CHURN] Top {len(result['high_churn_services'])} Services:")
    for i, service in enumerate(result['high_churn_services'], 1):
        print(f"   {i}. {service}")
    print()
    
    print(f"[CONTRIBUTORS] Top {len(result['top_contributors'])} Contributors:")
    for i, contributor in enumerate(result['top_contributors'], 1):
        print(f"   {i}. {contributor}")
    print()
    
    print("=" * 70)
    print()
    
    # Show what the state would look like after this node
    print("Updated State Keys:")
    print("-" * 70)
    print(f"  high_churn_services: {result['high_churn_services']}")
    print(f"  recent_commits: {result['recent_commits']}")
    print(f"  top_contributors: {result['top_contributors']}")
    print()
    
    return result


if __name__ == "__main__":
    try:
        demo_git_history_analysis()
        print("[SUCCESS] Demo completed successfully!")
        print()
        print("Note: If GitPython is not installed, fallback data is used.")
        print("Install with: pip install gitpython")
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()


# Made with Bob