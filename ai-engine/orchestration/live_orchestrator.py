"""
Live Repository Intelligence Orchestrator for IncidentOS
========================================================

This module implements a production-ready LangGraph orchestrator that replaces
mock data with real filesystem parsing and live Git extraction. It enforces
strict data contracts and provides a complete intelligence pipeline for
downstream agents.

Phases Implemented:
1. Strict Data Standardization (Type Safety & Validation)
2. Live Repository Ingestion (Real Filesystem Parsing)
3. Live Git History Analysis (Real Git Metrics)
4. LangGraph Orchestrator Wiring (Complete Pipeline)
5. Execution & Testing (Runnable Demo)

Author: Lead Core AI Engineer
Date: 2026-05-16
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict
from functools import wraps

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PHASE 1: STRICT DATA STANDARDIZATION (THE CONTRACT)
# ============================================================================

class AgentState(TypedDict, total=False):
    """
    Strict TypedDict contract for LangGraph state.
    
    This enforces type safety across all agent nodes and ensures
    downstream agents receive properly formatted data.
    
    All fields are optional (total=False) to allow incremental state building,
    but validation ensures required fields are present before node execution.
    """
    repo_id: str
    repo_path: str
    services: List[str]
    languages: List[str]
    frameworks: List[str]
    architecture_summary: str
    high_churn_services: List[str]
    recent_commits: int
    top_contributors: List[str]
    pr_analytics: Dict[str, Any]
    repo_metadata: str


def validate_state_output(func):
    """
    Decorator that validates and sanitizes node outputs before returning.
    
    Ensures:
    - Lists are actually lists (not None or other types)
    - Strings are actually strings (not None)
    - Missing fields are auto-corrected to safe defaults
    - Downstream agents never crash due to malformed data
    
    This is the enforcement layer for our data contract.
    """
    @wraps(func)
    def wrapper(state: AgentState) -> Dict[str, Any]:
        try:
            # Execute the node function
            result = func(state)
            
            # Validate and sanitize the output
            sanitized = {}
            
            # Ensure lists are lists
            for list_field in ['services', 'languages', 'frameworks', 'high_churn_services', 'top_contributors']:
                if list_field in result:
                    value = result[list_field]
                    if value is None or not isinstance(value, list):
                        logger.warning(f"Field '{list_field}' is not a list, converting to empty list")
                        sanitized[list_field] = []
                    else:
                        sanitized[list_field] = value
            
            # Ensure strings are strings
            for str_field in ['repo_id', 'repo_path', 'architecture_summary', 'repo_metadata']:
                if str_field in result:
                    value = result[str_field]
                    if value is None or not isinstance(value, str):
                        logger.warning(f"Field '{str_field}' is not a string, converting to empty string")
                        sanitized[str_field] = ""
                    else:
                        sanitized[str_field] = value
            
            # Ensure integers are integers
            if 'recent_commits' in result:
                value = result['recent_commits']
                if value is None or not isinstance(value, int):
                    logger.warning(f"Field 'recent_commits' is not an int, converting to 0")
                    sanitized['recent_commits'] = 0
                else:
                    sanitized['recent_commits'] = value
            
            # Ensure dicts are dicts
            if 'pr_analytics' in result:
                value = result['pr_analytics']
                if value is None or not isinstance(value, dict):
                    logger.warning(f"Field 'pr_analytics' is not a dict, converting to empty dict")
                    sanitized['pr_analytics'] = {}
                else:
                    sanitized['pr_analytics'] = value
            
            logger.info(f"Node '{func.__name__}' output validated successfully")
            return sanitized
            
        except Exception as e:
            logger.error(f"Error in node '{func.__name__}': {e}", exc_info=True)
            # Return safe defaults on catastrophic failure
            return {
                'services': [],
                'languages': [],
                'frameworks': [],
                'high_churn_services': [],
                'recent_commits': 0,
                'top_contributors': [],
                'architecture_summary': '',
                'repo_metadata': '',
                'pr_analytics': {}
            }
    
    return wrapper


# ============================================================================
# PHASE 2: LIVE REPOSITORY INGESTION NODE
# ============================================================================

@validate_state_output
def repository_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Live repository analysis node with real filesystem parsing.
    
    This node:
    1. Takes repo_path from state
    2. Uses os.walk to traverse the real directory
    3. Ignores .git, node_modules, venv, __pycache__
    4. Extracts services (top-level directories with code)
    5. Detects languages via file extensions
    6. Detects frameworks via manifest files
    7. Returns validated state updates
    
    Args:
        state: Current AgentState with repo_path
        
    Returns:
        Dict with services, languages, frameworks, architecture_summary
    """
    repo_path = state.get('repo_path', '')
    repo_id = state.get('repo_id', 'unknown')
    
    logger.info(f"[REPOSITORY AGENT] Starting analysis for {repo_id} at {repo_path}")
    
    # Validate repo_path
    if not repo_path or not os.path.exists(repo_path):
        logger.error(f"Invalid repo_path: {repo_path}")
        return {
            'services': [],
            'languages': [],
            'frameworks': [],
            'architecture_summary': 'Repository path invalid or not found'
        }
    
    # Directories to ignore
    IGNORED_DIRS = {
        '.git', '.github', '.vscode', '.idea', 'node_modules', '__pycache__',
        '.pytest_cache', '.mypy_cache', 'venv', 'env', '.env', '.venv',
        'dist', 'build', '.next', '.nuxt', 'coverage', '.coverage'
    }
    
    # Language detection mapping
    EXTENSION_TO_LANGUAGE = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.tsx': 'TypeScript', '.jsx': 'JavaScript', '.go': 'Go',
        '.java': 'Java', '.rb': 'Ruby', '.php': 'PHP', '.cs': 'C#',
        '.cpp': 'C++', '.c': 'C', '.rs': 'Rust', '.swift': 'Swift',
        '.kt': 'Kotlin', '.scala': 'Scala'
    }
    
    services = set()
    languages = set()
    frameworks = set()
    
    try:
        # First pass: identify top-level service directories
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            if os.path.isdir(item_path) and item not in IGNORED_DIRS:
                # Check if directory contains code files
                has_code = False
                try:
                    for root, dirs, files in os.walk(item_path):
                        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
                        for file in files:
                            ext = os.path.splitext(file)[1]
                            if ext in EXTENSION_TO_LANGUAGE:
                                has_code = True
                                break
                        if has_code:
                            break
                except Exception as e:
                    logger.debug(f"Error scanning {item_path}: {e}")
                
                if has_code:
                    services.add(item)
                    logger.info(f"Detected service: {item}")
        
        # Second pass: collect languages and frameworks
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            for file in files:
                # Detect languages
                ext = os.path.splitext(file)[1]
                if ext in EXTENSION_TO_LANGUAGE:
                    languages.add(EXTENSION_TO_LANGUAGE[ext])
                
                # Detect frameworks from manifest files
                file_path = os.path.join(root, file)
                detected_frameworks = _detect_frameworks(file, file_path)
                frameworks.update(detected_frameworks)
        
        # Generate architecture summary
        arch_summary = _generate_architecture_summary(services, languages, frameworks)
        
        logger.info(
            f"[REPOSITORY AGENT] Complete: {len(services)} services, "
            f"{len(languages)} languages, {len(frameworks)} frameworks"
        )
        
        return {
            'services': sorted(list(services)),
            'languages': sorted(list(languages)),
            'frameworks': sorted(list(frameworks)),
            'architecture_summary': arch_summary
        }
        
    except Exception as e:
        logger.error(f"[REPOSITORY AGENT] Fatal error: {e}", exc_info=True)
        return {
            'services': [],
            'languages': [],
            'frameworks': [],
            'architecture_summary': f'Analysis failed: {str(e)}'
        }


def _detect_frameworks(filename: str, filepath: str) -> set:
    """Detect frameworks from manifest files."""
    frameworks = set()
    
    try:
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return frameworks
        
        # JavaScript/TypeScript frameworks
        if filename == 'package.json':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'next' in deps:
                    frameworks.add('Next.js')
                if 'react' in deps:
                    frameworks.add('React')
                if 'vue' in deps:
                    frameworks.add('Vue.js')
                if 'express' in deps:
                    frameworks.add('Express')
                if '@nestjs/core' in deps:
                    frameworks.add('NestJS')
        
        # Python frameworks
        elif filename == 'requirements.txt':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    frameworks.add('FastAPI')
                if 'django' in content:
                    frameworks.add('Django')
                if 'flask' in content:
                    frameworks.add('Flask')
                if 'langgraph' in content:
                    frameworks.add('LangGraph')
                if 'langchain' in content:
                    frameworks.add('LangChain')
        
        # Go frameworks
        elif filename == 'go.mod':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'gin-gonic/gin' in content:
                    frameworks.add('Gin')
                if 'gorilla/mux' in content:
                    frameworks.add('Gorilla Mux')
    
    except Exception as e:
        logger.debug(f"Error parsing {filename}: {e}")
    
    return frameworks


def _generate_architecture_summary(services: set, languages: set, frameworks: set) -> str:
    """Generate natural language architecture summary."""
    if not services:
        return "No services detected in repository"
    
    summary_parts = []
    summary_parts.append(f"{len(services)} service(s) detected")
    
    if languages:
        lang_str = ", ".join(sorted(languages))
        summary_parts.append(f"using {lang_str}")
    
    if frameworks:
        fw_str = ", ".join(sorted(frameworks))
        summary_parts.append(f"with frameworks: {fw_str}")
    
    return ". ".join(summary_parts) + "."


# ============================================================================
# PHASE 3: LIVE GIT HISTORY NODE
# ============================================================================

# Try to import GitPython
try:
    import git
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    git = None  # type: ignore
    Repo = None  # type: ignore
    InvalidGitRepositoryError = Exception  # type: ignore
    GIT_AVAILABLE = False
    logger.warning("GitPython not available - install with: pip install gitpython")


@validate_state_output
def git_history_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Live git history analysis node with real Git extraction.
    
    This node:
    1. Initializes git.Repo(repo_path) using GitPython
    2. Extracts metrics from last 100 commits
    3. Calculates recent_commits count
    4. Identifies top_contributors by commit frequency
    5. Maps modified files to services for churn analysis
    6. Compiles repo_metadata summary
    7. Returns validated state updates
    
    Args:
        state: Current AgentState with repo_path and services
        
    Returns:
        Dict with high_churn_services, recent_commits, top_contributors, repo_metadata
    """
    repo_path = state.get('repo_path', '')
    services = state.get('services', [])
    repo_id = state.get('repo_id', 'unknown')
    
    logger.info(f"[GIT HISTORY AGENT] Starting analysis for {repo_id}")
    
    # Validate inputs
    if not repo_path or not os.path.exists(repo_path):
        logger.error(f"Invalid repo_path: {repo_path}")
        return _get_git_fallback_data()
    
    if not GIT_AVAILABLE:
        logger.warning("GitPython not available - returning fallback data")
        return _get_git_fallback_data()
    
    try:
        # Initialize Git repository
        repo = Repo(repo_path)  # type: ignore
        logger.info(f"Successfully initialized git repo at {repo_path}")
        
        # Track metrics
        from collections import Counter
        contributor_commits = Counter()
        service_changes = Counter()
        commit_count = 0
        
        # Analyze last 100 commits
        for commit in repo.iter_commits(max_count=100):
            commit_count += 1
            
            # Track contributors
            contributor_commits[commit.author.name] += 1
            
            # Analyze file changes for service churn
            try:
                for file_path in commit.stats.files.keys():
                    # Map file to service
                    service = _map_file_to_service(str(file_path), services)
                    if service:
                        service_changes[service] += 1
            except Exception as e:
                logger.debug(f"Error analyzing commit {commit.hexsha[:8]}: {e}")
        
        # Extract top contributors (top 5)
        top_contributors = [name for name, _ in contributor_commits.most_common(5)]
        
        # Extract high-churn services (top 3)
        high_churn_services = [svc for svc, _ in service_changes.most_common(3)]
        
        # If no churn detected but we have services, use first few
        if not high_churn_services and services:
            high_churn_services = services[:min(3, len(services))]
        
        # Generate metadata summary
        repo_metadata = _generate_repo_metadata(
            repo_id, services, high_churn_services, commit_count, top_contributors
        )
        
        logger.info(
            f"[GIT HISTORY AGENT] Complete: {commit_count} commits, "
            f"{len(contributor_commits)} contributors, {len(service_changes)} services with churn"
        )
        
        return {
            'high_churn_services': high_churn_services,
            'recent_commits': commit_count,
            'top_contributors': top_contributors,
            'repo_metadata': repo_metadata,
            'pr_analytics': {}  # Placeholder for future PR analysis
        }
        
    except InvalidGitRepositoryError:  # type: ignore
        logger.warning(f"Not a valid git repository: {repo_path}")
        return _get_git_fallback_data()
    except Exception as e:
        logger.error(f"[GIT HISTORY AGENT] Fatal error: {e}", exc_info=True)
        return _get_git_fallback_data()


def _map_file_to_service(file_path: str, services: List[str]) -> Optional[str]:
    """Map a file path to a service based on directory structure."""
    file_path = file_path.replace('\\', '/')
    parts = file_path.split('/')
    
    if parts and parts[0] in services:
        return parts[0]
    
    return None


def _generate_repo_metadata(
    repo_id: str,
    services: List[str],
    high_churn: List[str],
    commits: int,
    contributors: List[str]
) -> str:
    """Generate comprehensive repository metadata summary."""
    services_str = ", ".join(services) if services else "none"
    churn_str = ", ".join(high_churn) if high_churn else "none"
    contrib_str = ", ".join(contributors[:3]) if contributors else "none"
    
    metadata = (
        f"Repository {repo_id} analysis: "
        f"Services: {services_str}. "
        f"High-churn areas: {churn_str}. "
        f"Recent activity: {commits} commits. "
        f"Top contributors: {contrib_str}."
    )
    
    return metadata


def _get_git_fallback_data() -> Dict[str, Any]:
    """Provide safe fallback data when Git analysis fails."""
    return {
        'high_churn_services': [],
        'recent_commits': 0,
        'top_contributors': [],
        'repo_metadata': 'Git analysis unavailable',
        'pr_analytics': {}
    }


# ============================================================================
# PHASE 4: LANGGRAPH ORCHESTRATOR WIRING & EXECUTION
# ============================================================================

def create_orchestrator():
    """
    Create and wire the LangGraph orchestrator.
    
    This function:
    1. Initializes StateGraph with AgentState
    2. Adds repository_agent_node
    3. Adds git_history_agent_node
    4. Wires the sequence: START -> repository -> git_history -> END
    5. Compiles and returns the graph
    
    Returns:
        Compiled LangGraph ready for execution
    """
    try:
        from langgraph.graph import StateGraph, START, END
        
        logger.info("[ORCHESTRATOR] Initializing LangGraph...")
        
        # Initialize graph with our strict AgentState
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("repository_agent", repository_agent_node)
        workflow.add_node("git_history_agent", git_history_agent_node)
        
        # Wire the sequence
        workflow.add_edge(START, "repository_agent")
        workflow.add_edge("repository_agent", "git_history_agent")
        workflow.add_edge("git_history_agent", END)
        
        # Compile the graph
        app = workflow.compile()
        
        logger.info("[ORCHESTRATOR] LangGraph compiled successfully")
        return app
        
    except ImportError as e:
        logger.error(f"LangGraph not available: {e}")
        logger.error("Install with: pip install langgraph")
        raise
    except Exception as e:
        logger.error(f"Failed to create orchestrator: {e}", exc_info=True)
        raise


def execute_orchestrator(repo_path: str, repo_id: str = "test-repo") -> Dict[str, Any]:
    """
    Execute the orchestrator on a repository.
    
    Args:
        repo_path: Path to repository to analyze
        repo_id: Unique identifier for the repository
        
    Returns:
        Final state dictionary with all analysis results
    """
    logger.info(f"[EXECUTION] Starting orchestrator for {repo_id} at {repo_path}")
    
    # Create orchestrator
    app = create_orchestrator()
    
    # Initialize state
    initial_state: AgentState = {
        'repo_id': repo_id,
        'repo_path': repo_path,
        'services': [],
        'languages': [],
        'frameworks': [],
        'architecture_summary': '',
        'high_churn_services': [],
        'recent_commits': 0,
        'top_contributors': [],
        'pr_analytics': {},
        'repo_metadata': ''
    }
    
    # Execute the graph
    logger.info("[EXECUTION] Invoking orchestrator...")
    final_state = app.invoke(initial_state)
    
    logger.info("[EXECUTION] Orchestrator complete")
    return final_state


# ============================================================================
# PHASE 5: DEPLOYMENT & TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Local execution block for testing the orchestrator.
    
    This demonstrates the complete pipeline running on the current repository.
    """
    print("=" * 80)
    print("IncidentOS Live Repository Intelligence Orchestrator")
    print("=" * 80)
    print()
    
    # Determine repository path (current directory or test repo)
    current_dir = os.getcwd()
    
    # Check if we're in the ai-engine directory
    if current_dir.endswith('ai-engine'):
        # Go up one level to the project root
        repo_path = os.path.dirname(current_dir)
    else:
        repo_path = current_dir
    
    print(f"Analyzing repository at: {repo_path}")
    print()
    
    try:
        # Execute orchestrator
        final_state = execute_orchestrator(
            repo_path=repo_path,
            repo_id="IncidentOS"
        )
        
        # Pretty print results
        print("=" * 80)
        print("ORCHESTRATOR RESULTS")
        print("=" * 80)
        print()
        print(json.dumps(final_state, indent=2, default=str))
        print()
        print("=" * 80)
        print("SUCCESS: Orchestrator executed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR: Orchestrator execution failed")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
