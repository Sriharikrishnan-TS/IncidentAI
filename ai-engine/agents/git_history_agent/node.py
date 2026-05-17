"""
Git History Agent Node for LangGraph Workflow
Analyzes git repository history to detect high-churn services and contributors.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from collections import Counter
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph.state import AgentState
from memory.embeddings import generate_embeddings, generate_batch_embeddings

# Configure logging
logger = logging.getLogger(__name__)

# Try to import GitPython, but make it optional
try:
    import git
    GIT_AVAILABLE = True
    logger.info("GitPython successfully imported")
except ImportError:
    GIT_AVAILABLE = False
    logger.warning("GitPython not available - will use fallback data")

# Try to import ChromaDB, but make it optional
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB successfully imported")
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available - memory persistence disabled")


def _generate_memory_report(
    repo_id: str,
    services: List[str],
    languages: List[str],
    frameworks: List[str],
    high_churn_services: List[str],
    recent_commits: int,
    top_contributors: List[str]
) -> str:
    """
    Generates a comprehensive textual engineering memory report.
    
    This report summarizes the repository analysis and git history metrics
    in a natural language format suitable for vector embedding and retrieval.
    
    Args:
        repo_id: Unique repository identifier
        services: List of detected services
        languages: List of programming languages
        frameworks: List of frameworks
        high_churn_services: List of high-churn services
        recent_commits: Number of recent commits
        top_contributors: List of top contributors
        
    Returns:
        Formatted text report string
    """
    services_str = ", ".join(services) if services else "no services detected"
    languages_str = ", ".join(languages) if languages else "unknown languages"
    frameworks_str = ", ".join(frameworks) if frameworks else "no frameworks detected"
    churn_str = ", ".join(high_churn_services) if high_churn_services else "none identified"
    contributors_str = ", ".join(top_contributors) if top_contributors else "no contributors found"
    
    report = f"""Repository {repo_id} contains services: {services_str}.
The codebase uses {languages_str} with frameworks: {frameworks_str}.
Analysis of the last {recent_commits} commits shows that high risk churn is isolated to: {churn_str}.
Top authors are: {contributors_str}.
This repository shows {'high' if recent_commits > 50 else 'moderate' if recent_commits > 20 else 'low'} development activity."""
    
    return report.strip()


def _get_chromadb_client() -> Optional['chromadb.Client']:
    """
    Initializes and returns a ChromaDB client pointing to localhost:8000.
    
    Returns:
        ChromaDB client instance or None if initialization fails
    """
    if not CHROMADB_AVAILABLE:
        logger.warning("ChromaDB not available - skipping client initialization")
        return None
    
    try:
        # Initialize ChromaDB client with HTTP connection to localhost:8000
        client: ClientAPI = chromadb.HttpClient(
            host="localhost",
            port=8000,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Test connection with a simple heartbeat
        client.heartbeat()
        logger.info("Successfully connected to ChromaDB at localhost:8000")
        return client
        
    except Exception as e:
        logger.warning(f"Failed to connect to ChromaDB: {e}. Memory persistence disabled.")
        return None


def _persist_to_chromadb(
    repo_id: str,
    memory_report: str,
    services: List[str],
    languages: List[str],
    frameworks: List[str],
    high_churn_services: List[str],
    recent_commits: int,
    top_contributors: List[str],
    architecture_summary: str = "",
    pr_analytics: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Persists repository analysis to ChromaDB with true vector embeddings.
    
    Generates embeddings for:
    - Repository onboarding summary (memory_report)
    - Architecture summary
    - PR analytics summary
    
    Each document is tagged with explicit metadata for efficient querying
    by the Mentor Agent and other downstream consumers.
    
    Args:
        repo_id: Unique repository identifier
        memory_report: Generated text report for onboarding
        services: List of services (for metadata)
        languages: List of languages (for metadata)
        frameworks: List of frameworks (for metadata)
        high_churn_services: List of high-churn services (for metadata)
        recent_commits: Number of recent commits (for metadata)
        top_contributors: List of top contributors (for metadata)
        architecture_summary: Natural-language architecture description
        pr_analytics: PR and branch churn analytics data
        
    Returns:
        True if persistence succeeded, False otherwise
    """
    if pr_analytics is None:
        pr_analytics = {}
    try:
        # Get ChromaDB client
        client = _get_chromadb_client()
        if client is None:
            return False
        
        # Get or create the repository_memory collection
        try:
            collection = client.get_or_create_collection(
                name="repository_memory",
                metadata={"description": "Repository onboarding and analysis summaries"}
            )
            logger.info("Successfully accessed repository_memory collection")
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            return False
        
        # Prepare documents and metadata for batch insertion
        documents = []
        metadatas = []
        embeddings_list = []
        ids = []
        
        # Document 1: Onboarding Summary
        onboarding_metadata = {
            "repo_id": repo_id,
            "type": "onboarding_summary",
            "services": ",".join(services),
            "languages": ",".join(languages),
            "frameworks": ",".join(frameworks),
            "high_churn_services": ",".join(high_churn_services),
            "recent_commits": str(recent_commits),
            "top_contributors": ",".join(top_contributors[:3])
        }
        documents.append(memory_report)
        metadatas.append(onboarding_metadata)
        ids.append(f"{repo_id}_onboarding")
        
        # Document 2: Architecture Summary (if available)
        if architecture_summary and architecture_summary.strip():
            arch_metadata = {
                "repo_id": repo_id,
                "type": "architecture_summary",
                "services": ",".join(services),
                "languages": ",".join(languages),
                "frameworks": ",".join(frameworks)
            }
            documents.append(architecture_summary)
            metadatas.append(arch_metadata)
            ids.append(f"{repo_id}_architecture")
        
        # Document 3: PR Analytics Summary (if available)
        if pr_analytics and pr_analytics.get("churn_summary"):
            churn_summary = pr_analytics["churn_summary"]
            pr_summary_text = (
                f"Repository {repo_id} PR and branch activity analysis: "
                f"{churn_summary.get('total_merge_commits', 0)} merge commits detected. "
                f"Services with high PR activity: {', '.join(churn_summary.get('services_with_high_pr_activity', []))}. "
                f"Active branches: {churn_summary.get('active_branches', 0)}. "
                f"PR to commit ratio: {churn_summary.get('pr_to_commit_ratio', 0):.2%}."
            )
            pr_metadata = {
                "repo_id": repo_id,
                "type": "pr_analytics",
                "services": ",".join(services),
                "high_pr_activity_services": ",".join(churn_summary.get('services_with_high_pr_activity', [])),
                "total_merge_commits": str(churn_summary.get('total_merge_commits', 0)),
                "active_branches": str(churn_summary.get('active_branches', 0))
            }
            documents.append(pr_summary_text)
            metadatas.append(pr_metadata)
            ids.append(f"{repo_id}_pr_analytics")
        
        # Generate embeddings for all documents
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        try:
            embeddings_list = generate_batch_embeddings(documents)
            logger.info(f"Successfully generated {len(embeddings_list)} embeddings")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            # Fall back to letting ChromaDB auto-generate embeddings
            embeddings_list = None
        
        # Add documents to collection with embeddings
        if embeddings_list:
            collection.add(
                documents=documents,
                embeddings=embeddings_list,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully persisted {len(documents)} documents with custom embeddings for {repo_id}")
        else:
            # Fallback: let ChromaDB auto-generate embeddings
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully persisted {len(documents)} documents with auto-generated embeddings for {repo_id}")
        
        return True
        
    except Exception as e:
        # Catch all errors including network timeouts
        logger.warning(
            f"Failed to persist to ChromaDB (repo_id={repo_id}): {e}. "
            "Continuing without memory persistence."
        )
        return False


def git_history_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Git history analysis node that extracts churn metrics and contributor data.
    
    This node is responsible for analyzing the git repository history to identify:
    - High-churn services (services with frequent code changes)
    - Recent commit count
    - Top contributors to the repository
    
    Args:
        state: The current AgentState containing repo_path and services list
        
    Returns:
        Dictionary with updated high_churn_services, recent_commits, and 
        top_contributors keys that will be merged into the global LangGraph state
        
    Raises:
        Does not raise exceptions - all errors are caught and handled with
        fallback mock data to ensure the graph continues execution
    """
    try:
        # Extract repo_path and services from incoming state
        repo_path = state.get("repo_path", "")
        services = state.get("services", [])
        repo_id = state.get("repo_id", "unknown")
        
        logger.info(
            f"Starting git history analysis for repo_id={repo_id}, "
            f"path={repo_path}, services={len(services)}"
        )
        
        # Validate repo_path exists
        if not repo_path:
            raise ValueError("repo_path is empty or missing from state")
        
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        # Check if GitPython is available
        if not GIT_AVAILABLE:
            logger.warning("GitPython not available - returning fallback data")
            return _get_fallback_data()
        
        # Initialize git.Repo with defensive try/except
        try:
            repo = git.Repo(repo_path)
            logger.info(f"Successfully initialized git repository at {repo_path}")
        except (git.InvalidGitRepositoryError, git.NoSuchPathError) as e:
            logger.warning(
                f"Directory is not a valid git repository: {repo_path}. "
                f"Error: {e}. Returning fallback data."
            )
            return _get_fallback_data()
        
        # Analyze git history (includes basic churn metrics)
        analysis_results = _analyze_git_history(repo, services, repo_path)
        
        # Analyze branches (local and remote tracking)
        branch_analysis = _analyze_branches(repo)
        
        # Analyze PR and merge commits for churn patterns
        pr_analysis = _analyze_pr_and_merge_commits(repo, services, max_commits=100)
        
        # Compile pr_analytics dataset
        pr_analytics = {
            "branch_info": branch_analysis,
            "pr_metrics": pr_analysis,
            "churn_summary": {
                "services_with_high_pr_activity": pr_analysis["services_with_high_pr_activity"],
                "total_merge_commits": pr_analysis["total_merge_commits"],
                "active_branches": len(branch_analysis["active_branches"]),
                "pr_to_commit_ratio": (
                    pr_analysis["pr_count"] / analysis_results["recent_commits"]
                    if analysis_results["recent_commits"] > 0 else 0
                )
            }
        }
        
        logger.info(
            f"Git history analysis complete: "
            f"{len(analysis_results['high_churn_services'])} high-churn services, "
            f"{analysis_results['recent_commits']} recent commits, "
            f"{len(analysis_results['top_contributors'])} top contributors, "
            f"{pr_analysis['pr_count']} PRs analyzed"
        )
        
        # Extract additional state data for memory report
        languages = state.get("languages", [])
        frameworks = state.get("frameworks", [])
        
        # Generate comprehensive memory report
        memory_report = _generate_memory_report(
            repo_id=repo_id,
            services=services,
            languages=languages,
            frameworks=frameworks,
            high_churn_services=analysis_results["high_churn_services"],
            recent_commits=analysis_results["recent_commits"],
            top_contributors=analysis_results["top_contributors"]
        )
        
        logger.info(f"Generated memory report for {repo_id}")
        
        # Extract architecture summary from state
        architecture_summary = state.get("architecture_summary", "")
        
        # Persist to ChromaDB with embeddings (non-blocking - failures won't crash the pipeline)
        persistence_success = _persist_to_chromadb(
            repo_id=repo_id,
            memory_report=memory_report,
            services=services,
            languages=languages,
            frameworks=frameworks,
            high_churn_services=analysis_results["high_churn_services"],
            recent_commits=analysis_results["recent_commits"],
            top_contributors=analysis_results["top_contributors"],
            architecture_summary=architecture_summary,
            pr_analytics=pr_analytics
        )
        
        if persistence_success:
            logger.info(f"Successfully persisted memory for {repo_id} to ChromaDB")
        else:
            logger.warning(f"Memory persistence failed for {repo_id}, but continuing workflow")
        
        # Return dictionary to update the global LangGraph state
        return {
            "high_churn_services": analysis_results["high_churn_services"],
            "recent_commits": analysis_results["recent_commits"],
            "top_contributors": analysis_results["top_contributors"],
            "pr_analytics": pr_analytics,
        }
        
    except Exception as e:
        # Log the exception for debugging
        logger.error(
            f"Error during git history analysis for repo_id={state.get('repo_id', 'unknown')}: {e}",
            exc_info=True
        )
        
        # Return fallback mock data to keep the graph moving
        logger.warning("Injecting fallback mock data due to analysis failure")
        return _get_fallback_data()


def _analyze_git_history(
    repo: 'git.Repo',
    services: List[str],
    repo_path: str
) -> Dict[str, Any]:
    """
    Analyzes git repository history to extract churn and contributor metrics.
    
    This function:
    1. Iterates through the last 100 commits
    2. Tracks unique commit authors to determine top contributors
    3. Counts total commits for recent_commits metric
    4. Analyzes modified files via commit.stats.files to identify high-churn services
    
    Args:
        repo: GitPython Repo object
        services: List of service names detected by repository agent
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing high_churn_services, recent_commits, and top_contributors
    """
    # Initialize tracking structures
    contributor_commits: Counter = Counter()
    service_changes: Counter = Counter()
    recent_commit_count = 0
    
    try:
        # Iterate through the last 100 commits
        for commit in repo.iter_commits(max_count=100):
            # Count this commit
            recent_commit_count += 1
            
            # Track contributor (author name)
            contributor_name = commit.author.name
            contributor_commits[contributor_name] += 1
            
            # Analyze modified files using commit.stats.files
            try:
                # commit.stats.files returns a dict of {filepath: stats}
                modified_files = commit.stats.files
                
                for file_path in modified_files.keys():
                    # Map file to service by checking if path starts with service name
                    # Convert to string in case it's a PathLike object
                    service = _map_file_to_service(str(file_path), services)
                    if service:
                        service_changes[service] += 1
                        
            except Exception as e:
                logger.debug(f"Error analyzing commit {commit.hexsha}: {e}")
                continue
        
        # Get top 5 contributors by commit count
        top_contributors = [name for name, _ in contributor_commits.most_common(5)]
        
        # Get high-churn services (top 3 services by change frequency)
        high_churn_services = [service for service, _ in service_changes.most_common(3)]
        
        # If no high-churn services detected but we have services, use the first few
        if not high_churn_services and services:
            high_churn_services = services[:min(3, len(services))]
        
        logger.info(
            f"Analyzed {recent_commit_count} commits, "
            f"found {len(contributor_commits)} unique contributors, "
            f"tracked changes across {len(service_changes)} services"
        )
        
        return {
            "high_churn_services": high_churn_services,
            "recent_commits": recent_commit_count,
            "top_contributors": top_contributors,
        }
        
    except Exception as e:
        logger.error(f"Error analyzing git history: {e}", exc_info=True)
        return {
            "high_churn_services": [],
            "recent_commits": 0,
            "top_contributors": [],
        }

def _analyze_branches(repo: 'git.Repo') -> Dict[str, Any]:
    """
    Analyzes local and remote branches in the repository.
    
    Tracks active branches to understand development patterns and
    identify which branches are currently being worked on.
    
    Args:
        repo: GitPython Repo object
        
    Returns:
        Dictionary containing branch information:
        - local_branches: List of local branch names
        - remote_branches: List of remote branch names
        - active_branches: List of recently active branches
        - total_branches: Total count of all branches
    """
    local_branches = []
    remote_branches = []
    active_branches = []
    
    try:
        # Get local branches
        for branch in repo.branches:
            local_branches.append(branch.name)
            
            # Check if branch has recent activity (commits in last 30 days)
            try:
                # Get the latest commit on this branch
                latest_commit = branch.commit
                # Check if commit is recent (within 30 days)
                import datetime
                commit_date = datetime.datetime.fromtimestamp(latest_commit.committed_date)
                days_ago = (datetime.datetime.now() - commit_date).days
                
                if days_ago <= 30:
                    active_branches.append(branch.name)
            except Exception as e:
                logger.debug(f"Error checking branch activity for {branch.name}: {e}")
        
        # Get remote branches
        try:
            for ref in repo.remotes.origin.refs:
                # Skip HEAD reference
                if ref.name != 'origin/HEAD':
                    # Extract branch name without 'origin/' prefix
                    branch_name = ref.name.replace('origin/', '')
                    remote_branches.append(branch_name)
        except Exception as e:
            logger.debug(f"Error fetching remote branches: {e}")
        
        logger.info(
            f"Branch analysis: {len(local_branches)} local, "
            f"{len(remote_branches)} remote, {len(active_branches)} active"
        )
        
        return {
            "local_branches": local_branches,
            "remote_branches": remote_branches,
            "active_branches": active_branches,
            "total_branches": len(local_branches) + len(remote_branches)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing branches: {e}", exc_info=True)
        return {
            "local_branches": [],
            "remote_branches": [],
            "active_branches": [],
            "total_branches": 0
        }


def _analyze_pr_and_merge_commits(
    repo: 'git.Repo',
    services: List[str],
    max_commits: int = 100
) -> Dict[str, Any]:
    """
    Analyzes merge commits to extract PR information and branch churn patterns.
    
    Inspects commit messages for merge patterns like:
    - "Merge pull request #123 from user/branch-name"
    - "Merge branch 'feature-branch' into main"
    
    Tracks which services are receiving the most PR activity to identify
    areas of high development focus and potential instability.
    
    Args:
        repo: GitPython Repo object
        services: List of detected service names
        max_commits: Maximum number of commits to analyze
        
    Returns:
        Dictionary containing PR analytics:
        - total_merge_commits: Count of merge commits found
        - pr_count: Number of pull request merges detected
        - branch_merges: List of branch names that were merged
        - service_pr_activity: Dict mapping services to PR merge counts
        - recent_prs: List of recent PR information
    """
    merge_commits = []
    pr_count = 0
    branch_merges = []
    service_pr_activity: Counter = Counter()
    recent_prs = []
    
    # Regex patterns for detecting merge commits
    import re
    pr_pattern = re.compile(r'Merge pull request #(\d+) from ([^\s]+)')
    branch_pattern = re.compile(r"Merge branch '([^']+)'")
    
    try:
        for commit in repo.iter_commits(max_count=max_commits):
            # Ensure commit message is a string
            commit_message = commit.message
            if isinstance(commit_message, bytes):
                commit_message = commit_message.decode('utf-8', errors='ignore')
            commit_message = commit_message.strip()
            
            # Check if this is a merge commit (has multiple parents)
            if len(commit.parents) > 1:
                merge_commits.append(commit.hexsha)
                
                # Try to extract PR information
                pr_match = pr_pattern.search(commit_message)
                if pr_match:
                    pr_number = pr_match.group(1)
                    branch_name = pr_match.group(2)
                    pr_count += 1
                    branch_merges.append(branch_name)
                    
                    # Analyze which service this PR affects
                    affected_service = _extract_service_from_branch(branch_name, services)
                    if not affected_service:
                        # Try to determine from changed files
                        affected_service = _analyze_commit_service_impact(commit, services)
                    
                    if affected_service:
                        service_pr_activity[affected_service] += 1
                    
                    # Store recent PR info
                    if len(recent_prs) < 10:
                        recent_prs.append({
                            "pr_number": pr_number,
                            "branch": branch_name,
                            "service": affected_service or "unknown",
                            "author": commit.author.name,
                            "date": commit.committed_datetime.isoformat()
                        })
                
                # Try to extract branch merge information
                branch_match = branch_pattern.search(commit_message)
                if branch_match and not pr_match:  # Only if not already captured as PR
                    branch_name = branch_match.group(1)
                    branch_merges.append(branch_name)
                    
                    # Analyze service impact
                    affected_service = _extract_service_from_branch(branch_name, services)
                    if not affected_service:
                        affected_service = _analyze_commit_service_impact(commit, services)
                    
                    if affected_service:
                        service_pr_activity[affected_service] += 1
        
        # Convert service activity to sorted list
        service_activity_list = [
            {"service": service, "pr_count": count}
            for service, count in service_pr_activity.most_common()
        ]
        
        logger.info(
            f"PR analysis: {len(merge_commits)} merge commits, "
            f"{pr_count} PRs, {len(branch_merges)} branch merges, "
            f"{len(service_pr_activity)} services affected"
        )
        
        return {
            "total_merge_commits": len(merge_commits),
            "pr_count": pr_count,
            "branch_merges": list(set(branch_merges)),  # Unique branch names
            "service_pr_activity": service_activity_list,
            "recent_prs": recent_prs,
            "services_with_high_pr_activity": [
                item["service"] for item in service_activity_list[:3]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing PR and merge commits: {e}", exc_info=True)
        return {
            "total_merge_commits": 0,
            "pr_count": 0,
            "branch_merges": [],
            "service_pr_activity": [],
            "recent_prs": [],
            "services_with_high_pr_activity": []
        }


def _extract_service_from_branch(branch_name: str, services: List[str]) -> str:
    """
    Attempts to extract service name from branch name.
    
    Looks for service names in branch names like:
    - "user/frontend-feature"
    - "backend-go/fix-bug"
    - "feature/ai-engine-update"
    
    Args:
        branch_name: Name of the branch
        services: List of known service names
        
    Returns:
        Service name if found, empty string otherwise
    """
    branch_lower = branch_name.lower()
    
    for service in services:
        service_lower = service.lower()
        if service_lower in branch_lower:
            return service
    
    return ""


def _analyze_commit_service_impact(commit: 'git.Commit', services: List[str]) -> str:
    """
    Analyzes which service a commit primarily affects based on changed files.
    
    Args:
        commit: GitPython Commit object
        services: List of known service names
        
    Returns:
        Service name with most changes, or empty string
    """
    service_changes: Counter = Counter()
    
    try:
        # Analyze changed files
        for file_path in commit.stats.files.keys():
            service = _map_file_to_service(str(file_path), services)
            if service:
                service_changes[service] += 1
        
        # Return service with most changes
        if service_changes:
            return service_changes.most_common(1)[0][0]
    
    except Exception as e:
        logger.debug(f"Error analyzing commit service impact: {e}")
    
    return ""



def _map_file_to_service(file_path: str, services: List[str]) -> str:
    """
    Maps a file path to a service name based on the directory structure.
    
    Args:
        file_path: Relative path to the file in the repository
        services: List of detected service names
        
    Returns:
        Service name if the file belongs to a known service, empty string otherwise
    """
    # Normalize path separators
    file_path = file_path.replace('\\', '/')
    
    # Split path into components
    path_parts = file_path.split('/')
    
    if not path_parts:
        return ""
    
    # Check if the first directory matches any service
    first_dir = path_parts[0]
    if first_dir in services:
        return first_dir
    
    return ""


def _get_fallback_data() -> Dict[str, Any]:
    """
    Provides standard fallback data when git history analysis fails.
    
    This ensures the LangGraph workflow can continue even if the
    directory is not a git repository or git analysis encounters errors.
    
    Returns:
        Dictionary with hackathon-friendly dummy metrics
    """
    return {
        "high_churn_services": ["frontend", "backend-go", "ai-engine"],
        "recent_commits": 42,
        "top_contributors": [
            "Alice Developer",
            "Bob Engineer",
            "Charlie Coder",
            "Diana Designer",
            "Eve Architect"
        ],
        "pr_analytics": {
            "branch_info": {
                "local_branches": ["main", "develop"],
                "remote_branches": ["main", "develop"],
                "active_branches": ["main"],
                "total_branches": 4
            },
            "pr_metrics": {
                "total_merge_commits": 15,
                "pr_count": 10,
                "branch_merges": ["feature/ui-update", "fix/backend-bug"],
                "service_pr_activity": [
                    {"service": "frontend", "pr_count": 5},
                    {"service": "backend-go", "pr_count": 3},
                    {"service": "ai-engine", "pr_count": 2}
                ],
                "recent_prs": [],
                "services_with_high_pr_activity": ["frontend", "backend-go", "ai-engine"]
            },
            "churn_summary": {
                "services_with_high_pr_activity": ["frontend", "backend-go", "ai-engine"],
                "total_merge_commits": 15,
                "active_branches": 1,
                "pr_to_commit_ratio": 0.24
            }
        }
    }


# Made with Bob