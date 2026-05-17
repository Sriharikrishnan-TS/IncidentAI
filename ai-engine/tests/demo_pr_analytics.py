"""
Demo script to showcase PR and branch churn analytics.
"""
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.git_history_agent.node import git_history_agent_node
from graph.state import AgentState

def main():
    # Create initial state pointing to the IncidentOS repository
    state: AgentState = {
        "repo_id": "IncidentOS",
        "repo_path": str(Path(__file__).parent.parent.parent),
        "services": ["frontend", "backend-go", "ai-engine"],
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "Gin", "Next.js"],
        "architecture_summary": "Multi-service architecture",
        "high_churn_services": [],
        "recent_commits": 0,
        "top_contributors": [],
        "pr_analytics": {}
    }
    
    print("\n" + "="*70)
    print("IncidentOS PR and Branch Churn Analytics Demo")
    print("="*70 + "\n")
    
    # Run the git history agent
    result = git_history_agent_node(state)
    
    # Display basic git metrics
    print("Basic Git Metrics:")
    print(f"  Recent Commits: {result['recent_commits']}")
    print(f"  High Churn Services: {', '.join(result['high_churn_services'])}")
    print(f"  Top Contributors: {', '.join(result['top_contributors'][:3])}")
    
    # Display PR analytics
    pr_analytics = result['pr_analytics']
    
    print("\n" + "-"*70)
    print("Branch Information:")
    print("-"*70)
    branch_info = pr_analytics['branch_info']
    print(f"  Total Branches: {branch_info['total_branches']}")
    print(f"  Local Branches: {len(branch_info['local_branches'])}")
    if branch_info['local_branches']:
        print(f"    - {', '.join(branch_info['local_branches'][:5])}")
    print(f"  Remote Branches: {len(branch_info['remote_branches'])}")
    if branch_info['remote_branches']:
        print(f"    - {', '.join(branch_info['remote_branches'][:5])}")
    print(f"  Active Branches (last 30 days): {len(branch_info['active_branches'])}")
    if branch_info['active_branches']:
        print(f"    - {', '.join(branch_info['active_branches'])}")
    
    print("\n" + "-"*70)
    print("Pull Request Metrics:")
    print("-"*70)
    pr_metrics = pr_analytics['pr_metrics']
    print(f"  Total Merge Commits: {pr_metrics['total_merge_commits']}")
    print(f"  Pull Requests Analyzed: {pr_metrics['pr_count']}")
    print(f"  Unique Branch Merges: {len(pr_metrics['branch_merges'])}")
    if pr_metrics['branch_merges']:
        print(f"    Recent branches: {', '.join(pr_metrics['branch_merges'][:5])}")
    
    print("\n  Service PR Activity:")
    for activity in pr_metrics['service_pr_activity'][:5]:
        print(f"    - {activity['service']}: {activity['pr_count']} PRs")
    
    if pr_metrics['recent_prs']:
        print("\n  Recent Pull Requests:")
        for pr in pr_metrics['recent_prs'][:5]:
            print(f"    - PR #{pr['pr_number']}: {pr['branch']} -> {pr['service']} by {pr['author']}")
    
    print("\n" + "-"*70)
    print("Churn Summary (for Fragility Scoring):")
    print("-"*70)
    churn_summary = pr_analytics['churn_summary']
    print(f"  Services with High PR Activity:")
    for service in churn_summary['services_with_high_pr_activity']:
        print(f"    - {service}")
    print(f"  Total Merge Commits: {churn_summary['total_merge_commits']}")
    print(f"  Active Branches: {churn_summary['active_branches']}")
    print(f"  PR to Commit Ratio: {churn_summary['pr_to_commit_ratio']:.2%}")
    
    # Provide fragility insights
    print("\n" + "-"*70)
    print("Fragility Insights:")
    print("-"*70)
    pr_ratio = churn_summary['pr_to_commit_ratio']
    if pr_ratio > 0.4:
        print("  [HIGH] Very high PR activity - potential instability")
    elif pr_ratio > 0.25:
        print("  [MEDIUM] Moderate PR activity - active development")
    else:
        print("  [LOW] Low PR activity - stable codebase")
    
    if churn_summary['active_branches'] > 10:
        print("  [WARNING] Many active branches - potential merge conflicts")
    elif churn_summary['active_branches'] > 5:
        print("  [INFO] Several active branches - parallel development")
    else:
        print("  [GOOD] Few active branches - coordinated development")
    
    print("\n" + "="*70)
    print("\nPR Analytics Data Structure (JSON):")
    print("="*70)
    print(json.dumps(pr_analytics, indent=2, default=str))
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()

# Made with Bob
