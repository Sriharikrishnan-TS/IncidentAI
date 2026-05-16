"""
Demo script to test architecture extraction on the IncidentOS repository.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.repository_agent.node import repository_agent_node
from graph.state import AgentState

def main():
    # Create initial state pointing to the IncidentOS repository
    state: AgentState = {
        "repo_id": "IncidentOS",
        "repo_path": str(Path(__file__).parent.parent.parent),  # Go up to root
        "services": [],
        "languages": [],
        "frameworks": [],
        "architecture_summary": "",
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
        "pr_analytics": {}
    }
    
    print("\n" + "="*70)
    print("IncidentOS Repository Architecture Analysis")
    print("="*70 + "\n")
    
    # Run the repository agent
    result = repository_agent_node(state)
    
    # Display results
    print(f"Services Detected: {len(result['services'])}")
    for service in result['services']:
        print(f"  - {service}")
    
    print(f"\nLanguages Detected: {len(result['languages'])}")
    for lang in result['languages']:
        print(f"  - {lang}")
    
    print(f"\nFrameworks Detected: {len(result['frameworks'])}")
    for framework in result['frameworks']:
        print(f"  - {framework}")
    
    print("\n" + "-"*70)
    print("Architecture Summary:")
    print("-"*70)
    print(result['architecture_summary'])
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()

# Made with Bob
