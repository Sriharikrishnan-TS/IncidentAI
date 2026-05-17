"""
Demo script showcasing the complete Engineering Memory Layer with embeddings.

Demonstrates:
1. Repository analysis with architecture extraction
2. Git history with PR analytics
3. Vector embedding generation
4. ChromaDB persistence with proper metadata
5. Semantic similarity queries
"""
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.repository_agent.node import repository_agent_node
from agents.git_history_agent.node import git_history_agent_node
from graph.state import AgentState
from memory.embeddings import generate_embeddings, is_using_sentence_transformers


def main():
    print("\n" + "="*70)
    print("IncidentOS Engineering Memory Layer - Complete Demo")
    print("="*70 + "\n")
    
    # Step 1: Repository Analysis
    print("Step 1: Repository Analysis (Architecture Extraction)")
    print("-"*70)
    
    repo_path = str(Path(__file__).parent.parent.parent)
    
    initial_state: AgentState = {
        "repo_id": "IncidentOS",
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
    
    # Run repository agent
    repo_result = repository_agent_node(initial_state)
    
    print(f"  Services: {', '.join(repo_result['services'])}")
    print(f"  Languages: {', '.join(repo_result['languages'])}")
    print(f"  Frameworks: {', '.join(repo_result['frameworks'])}")
    print(f"  Architecture: {repo_result['architecture_summary'][:100]}...")
    
    # Step 2: Git History Analysis with PR Analytics
    print("\n" + "-"*70)
    print("Step 2: Git History Analysis (PR & Branch Churn)")
    print("-"*70)
    
    # Update state with repository results
    state_after_repo: AgentState = {
        **initial_state,
        **repo_result
    }
    
    # Run git history agent
    git_result = git_history_agent_node(state_after_repo)
    
    print(f"  Recent Commits: {git_result['recent_commits']}")
    print(f"  High Churn Services: {', '.join(git_result['high_churn_services'])}")
    print(f"  Top Contributors: {', '.join(git_result['top_contributors'][:3])}")
    
    pr_analytics = git_result['pr_analytics']
    print(f"  Total Branches: {pr_analytics['branch_info']['total_branches']}")
    print(f"  PRs Analyzed: {pr_analytics['pr_metrics']['pr_count']}")
    print(f"  PR/Commit Ratio: {pr_analytics['churn_summary']['pr_to_commit_ratio']:.2%}")
    
    # Step 3: Embedding Generation
    print("\n" + "-"*70)
    print("Step 3: Vector Embedding Generation")
    print("-"*70)
    
    print(f"  Embedding Engine: {'sentence-transformers' if is_using_sentence_transformers() else 'Fallback (hash-based)'}")
    
    # Generate embeddings for different document types
    documents = {
        "onboarding_summary": f"Repository IncidentOS contains services: {', '.join(repo_result['services'])}. "
                             f"Uses {', '.join(repo_result['languages'])} with {', '.join(repo_result['frameworks'])}.",
        "architecture_summary": repo_result['architecture_summary'],
        "pr_analytics": f"PR activity: {pr_analytics['pr_metrics']['pr_count']} PRs, "
                       f"{pr_analytics['churn_summary']['total_merge_commits']} merge commits"
    }
    
    embeddings = {}
    for doc_type, text in documents.items():
        embedding = generate_embeddings(text)
        embeddings[doc_type] = embedding
        print(f"  {doc_type}: {len(embedding)}-dimensional vector generated")
    
    # Step 4: ChromaDB Metadata Structure
    print("\n" + "-"*70)
    print("Step 4: ChromaDB Persistence Metadata")
    print("-"*70)
    
    metadata_examples = [
        {
            "repo_id": "IncidentOS",
            "type": "onboarding_summary",
            "services": ",".join(repo_result['services']),
            "languages": ",".join(repo_result['languages']),
            "frameworks": ",".join(repo_result['frameworks'])
        },
        {
            "repo_id": "IncidentOS",
            "type": "architecture_summary",
            "services": ",".join(repo_result['services']),
            "languages": ",".join(repo_result['languages'])
        },
        {
            "repo_id": "IncidentOS",
            "type": "pr_analytics",
            "services": ",".join(repo_result['services']),
            "high_pr_activity_services": ",".join(pr_analytics['churn_summary']['services_with_high_pr_activity']),
            "total_merge_commits": str(pr_analytics['churn_summary']['total_merge_commits'])
        }
    ]
    
    print("  Document metadata structure for ChromaDB:")
    for i, metadata in enumerate(metadata_examples, 1):
        print(f"\n  Document {i} ({metadata['type']}):")
        for key, value in metadata.items():
            print(f"    {key}: {value}")
    
    # Step 5: Semantic Query Examples
    print("\n" + "-"*70)
    print("Step 5: Semantic Query Capabilities")
    print("-"*70)
    
    query_examples = [
        "What services are in this repository?",
        "Which services have high code churn?",
        "What is the architecture of this system?",
        "How many pull requests were merged recently?"
    ]
    
    print("  Example queries that can be answered via similarity search:")
    for query in query_examples:
        query_embedding = generate_embeddings(query)
        print(f"    - '{query}'")
        print(f"      (Query embedded as {len(query_embedding)}-dimensional vector)")
    
    # Step 6: Complete Data Flow Summary
    print("\n" + "="*70)
    print("Complete Engineering Memory Layer Data Flow")
    print("="*70)
    
    print("""
  1. RepositoryAgent analyzes folder structure
     --> Extracts: services, languages, frameworks, architecture_summary
  
  2. GitHistoryAgent analyzes git history
     --> Extracts: commits, contributors, PR analytics, branch churn
  
  3. Memory report generated combining all analysis
     --> Natural language summaries for each aspect
  
  4. Embeddings generated for each document type
     --> Vector representations for semantic search
  
  5. ChromaDB persistence with metadata
     --> Documents stored with:
         * Vector embeddings for similarity search
         * Explicit metadata (repo_id, type, services, etc.)
         * Full text for retrieval
  
  6. Mentor Agent can query via:
     --> Semantic similarity: "What services have high churn?"
     --> Metadata filtering: type="architecture_summary"
     --> Combined queries for precise results
    """)
    
    print("="*70)
    print("\nEngineering Memory Layer is ready for:")
    print("  [OK] Semantic search across repository knowledge")
    print("  [OK] Onboarding new developers with context")
    print("  [OK] Fragility scoring using PR analytics")
    print("  [OK] Architecture understanding for incident response")
    print("="*70 + "\n")
    
    # Show sample embedding data
    print("Sample Embedding Data (first 10 dimensions):")
    print("-"*70)
    for doc_type, embedding in embeddings.items():
        print(f"  {doc_type}: {embedding[:10]}")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
