"""
Repository Agent Node for LangGraph Workflow
Analyzes repository structure to detect services, languages, and frameworks.
"""
import logging
import os
import json
from typing import Dict, Any, Set, List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph.state import AgentState
from parsers.import_parser import parse_imports_from_file, get_parser_status
from memory.repository_memory import get_repository_memory

# Configure logging
logger = logging.getLogger(__name__)

# Log parser status on module load
parser_status = get_parser_status()
logger.info(f"Import parser initialized: {parser_status}")

# Initialize repository memory
repository_memory = get_repository_memory()
logger.info(f"Repository memory initialized: {repository_memory.get_storage_stats()}")


def repository_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Repository analysis node that extracts metadata from a repository.
    
    This node is responsible for analyzing the repository structure and
    detecting services, programming languages, and frameworks used.
    
    Args:
        state: The current AgentState containing repo_id and repo_path
        
    Returns:
        Dictionary with updated services, languages, and frameworks keys
        that will be merged into the global LangGraph state
        
    Raises:
        Does not raise exceptions - all errors are caught and handled with
        fallback mock data to ensure the graph continues execution
    """
    try:
        # Extract repo_path from incoming state
        repo_path = state.get("repo_path", "")
        repo_id = state.get("repo_id", "unknown")
        
        logger.info(f"Starting repository analysis for repo_id={repo_id}, path={repo_path}")
        
        # Validate repo_path exists
        if not repo_path:
            raise ValueError("repo_path is empty or missing from state")
        
        # TODO: Replace this placeholder with actual analysis logic
        # This is where you would call your repository parsing/analysis wrapper
        analyzed_data = _analyze_repository(repo_path)
        
        # Extract results from analysis
        services = analyzed_data.get("services", [])
        languages = analyzed_data.get("languages", [])
        frameworks = analyzed_data.get("frameworks", [])
        imports = analyzed_data.get("imports", [])
        
        logger.info(
            f"Repository analysis complete: "
            f"{len(services)} services, {len(languages)} languages, "
            f"{len(frameworks)} frameworks, {len(imports)} imports"
        )
        
        # Store analysis results in repository memory before returning
        try:
            storage_success = repository_memory.store_repository_analysis(
                repo_id=repo_id,
                repo_path=repo_path,
                services=services,
                languages=languages,
                frameworks=frameworks,
                imports=imports
            )
            
            if storage_success:
                logger.info(f"Successfully persisted repository analysis to memory for {repo_id}")
            else:
                logger.warning(f"Failed to persist repository analysis to memory for {repo_id}")
                
        except Exception as storage_error:
            # Don't fail the node if storage fails - just log it
            logger.error(f"Error persisting to repository memory: {storage_error}", exc_info=True)
        
        # Return dictionary to update the global LangGraph state
        return {
            "services": services,
            "languages": languages,
            "frameworks": frameworks,
            "architecture_summary": analyzed_data.get("architecture_summary", ""),
        }
        
    except Exception as e:
        # Log the exception for debugging
        logger.error(
            f"Error during repository analysis for repo_id={state.get('repo_id', 'unknown')}: {e}",
            exc_info=True
        )
        
        # Return fallback mock data to keep the graph moving
        logger.warning("Injecting fallback mock data due to analysis failure")
        return _get_fallback_data()


def _analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    Analyzes repository structure to detect services, languages, and frameworks.
    
    This function scans the repository using os.walk to identify:
    - Services: Root-level directories containing code
    - Languages: Programming languages based on file extensions
    - Frameworks: Detected from manifest files (package.json, requirements.txt, etc.)
    - Architecture: Semantic classification of service roles and overall architecture
    
    Args:
        repo_path: Path to the repository to analyze
        
    Returns:
        Dictionary containing detected services, languages, frameworks, and architecture summary
    """
    logger.info(f"Scanning repository structure at: {repo_path}")
    scan_results = _scan_repo_structure(repo_path)
    
    return {
        "services": scan_results.get("services", []),
        "languages": scan_results.get("languages", []),
        "frameworks": scan_results.get("frameworks", []),
        "imports": scan_results.get("imports", []),
        "architecture_summary": scan_results.get("architecture_summary", ""),
    }


def _scan_repo_structure(repo_path: str) -> Dict[str, Any]:
    """
    Scans repository structure using os.walk to detect services, languages, frameworks,
    and performs semantic architecture extraction.
    
    This function:
    1. Identifies root-level directories as potential services (excluding utility folders)
    2. Collects file extensions to determine programming languages
    3. Parses manifest files to detect frameworks
    4. Classifies architectural roles of each service (REST API, Frontend, Microservice, etc.)
    5. Generates a natural-language architecture summary
    
    Args:
        repo_path: Path to the repository to scan
        
    Returns:
        Dictionary with services, languages, frameworks, and architecture_summary
    """
    # Directories to ignore (not considered services)
    IGNORED_DIRS = {
        '.git', '.github', '.vscode', '.idea', 'node_modules', '__pycache__',
        '.pytest_cache', '.mypy_cache', 'venv', 'env', '.env', '.venv', 'dist', 'build',
        '.next', '.nuxt', 'coverage', '.coverage', 'htmlcov', 'docs', 'doc',
        'tests', 'test', '__tests__', 'scripts', 'infra', 'repos', 'bob_sessions'
    }
    
    # File extensions to language mapping
    EXTENSION_TO_LANGUAGE = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.jsx': 'JavaScript',
        '.go': 'Go',
        '.java': 'Java',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'Objective-C',
        '.sh': 'Shell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.vue': 'Vue',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.pl': 'Perl',
    }
    
    services: Set[str] = set()
    languages: Set[str] = set()
    frameworks: Set[str] = set()
    all_imports: Set[str] = set()
    architecture_summary: str = ""  # Initialize to empty string
    
    # Track root-level directories and their architecture metadata
    root_dirs: Set[str] = set()
    service_architectures: Dict[str, str] = {}  # Maps service name to architecture role
    
    # Track files to parse for imports (limit to avoid performance issues)
    files_to_parse: List[str] = []
    MAX_FILES_TO_PARSE = 100
    
    try:
        # Validate repo_path exists and is accessible
        if not os.path.exists(repo_path):
            logger.error(f"Repository path does not exist: {repo_path}")
            return {
                "services": [],
                "languages": [],
                "frameworks": [],
                "imports": [],
            }
        
        if not os.path.isdir(repo_path):
            logger.error(f"Repository path is not a directory: {repo_path}")
            return {
                "services": [],
                "languages": [],
                "frameworks": [],
                "imports": [],
            }
        
        # First pass: identify root-level directories and classify their architecture
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            if os.path.isdir(item_path) and item not in IGNORED_DIRS:
                # Check if directory contains code files
                if _contains_code_files(item_path, EXTENSION_TO_LANGUAGE):
                    root_dirs.add(item)
                    services.add(item)
                    # Classify the architectural role of this service
                    arch_role = _classify_service_architecture(item_path, item)
                    if arch_role:
                        service_architectures[item] = arch_role
        
        # Second pass: walk through repository to collect languages and frameworks
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            # Detect languages from file extensions
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in EXTENSION_TO_LANGUAGE:
                    languages.add(EXTENSION_TO_LANGUAGE[ext])
                    
                    # Collect source files for import parsing (limit to avoid performance issues)
                    if len(files_to_parse) < MAX_FILES_TO_PARSE:
                        file_path = os.path.join(root, file)
                        files_to_parse.append(file_path)
                
                # Detect frameworks from manifest files
                file_path = os.path.join(root, file)
                detected_frameworks = _detect_frameworks_from_file(file, file_path)
                frameworks.update(detected_frameworks)
        
        # Third pass: parse imports from collected source files
        logger.info(f"Parsing imports from {len(files_to_parse)} source files...")
        for file_path in files_to_parse:
            try:
                imports = parse_imports_from_file(file_path)
                all_imports.update(imports)
            except Exception as e:
                logger.debug(f"Failed to parse imports from {file_path}: {e}")
        
        # Generate architecture summary
        architecture_summary = _generate_architecture_summary(service_architectures, services)
        
        logger.info(
            f"Scan complete: {len(services)} services, "
            f"{len(languages)} languages, {len(frameworks)} frameworks, "
            f"{len(all_imports)} unique imports"
        )
        logger.info(f"Architecture summary: {architecture_summary}")
        
    except Exception as e:
        logger.error(f"Error scanning repository structure: {e}", exc_info=True)
        # Return empty sets on error - will be converted to lists below
    
    return {
        "services": sorted(list(services)),
        "languages": sorted(list(languages)),
        "frameworks": sorted(list(frameworks)),
        "imports": sorted(list(all_imports)),
        "architecture_summary": architecture_summary,
    }


def _contains_code_files(directory: str, extension_map: Dict[str, str]) -> bool:
    """
    Checks if a directory contains any code files.
    
    Args:
        directory: Path to directory to check
        extension_map: Mapping of file extensions to languages
        
    Returns:
        True if directory contains code files, False otherwise
    """
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in extension_map:
                    return True
    except Exception:
        pass
    return False


def _detect_frameworks_from_file(filename: str, filepath: str) -> Set[str]:
    """
    Detects frameworks from manifest and configuration files.
    
    Analyzes files like package.json, requirements.txt, go.mod, etc.
    to identify frameworks and libraries in use.
    
    Args:
        filename: Name of the file
        filepath: Full path to the file
        
    Returns:
        Set of detected framework names
    """
    frameworks: Set[str] = set()
    
    try:
        # Validate file exists and is readable
        if not os.path.exists(filepath):
            return frameworks
        
        if not os.path.isfile(filepath):
            return frameworks
        
        # JavaScript/TypeScript frameworks from package.json
        if filename == 'package.json':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                # Check for popular frameworks
                if 'next' in dependencies:
                    frameworks.add('Next.js')
                if 'react' in dependencies:
                    frameworks.add('React')
                if 'vue' in dependencies:
                    frameworks.add('Vue.js')
                if 'angular' in dependencies or '@angular/core' in dependencies:
                    frameworks.add('Angular')
                if 'express' in dependencies:
                    frameworks.add('Express')
                if 'nestjs' in dependencies or '@nestjs/core' in dependencies:
                    frameworks.add('NestJS')
                if 'svelte' in dependencies:
                    frameworks.add('Svelte')
                if 'nuxt' in dependencies:
                    frameworks.add('Nuxt.js')
        
        # Python frameworks from requirements.txt or setup.py
        elif filename == 'requirements.txt':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    frameworks.add('FastAPI')
                if 'django' in content:
                    frameworks.add('Django')
                if 'flask' in content:
                    frameworks.add('Flask')
                if 'tornado' in content:
                    frameworks.add('Tornado')
                if 'pyramid' in content:
                    frameworks.add('Pyramid')
                if 'langgraph' in content:
                    frameworks.add('LangGraph')
                if 'langchain' in content:
                    frameworks.add('LangChain')
        
        # Go frameworks from go.mod
        elif filename == 'go.mod':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'gin-gonic/gin' in content:
                    frameworks.add('Gin')
                if 'gorilla/mux' in content:
                    frameworks.add('Gorilla Mux')
                if 'echo' in content:
                    frameworks.add('Echo')
                if 'fiber' in content:
                    frameworks.add('Fiber')
        
        # Ruby frameworks from Gemfile
        elif filename == 'Gemfile':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'rails' in content:
                    frameworks.add('Ruby on Rails')
                if 'sinatra' in content:
                    frameworks.add('Sinatra')
        
        # Java frameworks from pom.xml or build.gradle
        elif filename in ['pom.xml', 'build.gradle', 'build.gradle.kts']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if 'spring-boot' in content or 'springframework' in content:
                    frameworks.add('Spring Boot')
                if 'quarkus' in content:
                    frameworks.add('Quarkus')
                if 'micronaut' in content:
                    frameworks.add('Micronaut')
        
    except Exception as e:
        logger.debug(f"Error parsing {filename}: {e}")
    
    return frameworks


def _classify_service_architecture(service_path: str, service_name: str) -> str:
    """
    Classifies the architectural role of a service directory.
    
    Analyzes the service directory structure and contents to determine if it's:
    - REST_API_GATEWAY: Contains routing logic (routes/, @app.get, app.include_router)
    - MICROSERVICE_BACKEND: Backend service with API endpoints
    - FRONTEND_APPLICATION: Contains UI components (components/, pages/, app/)
    - DATA_LAYER: Database or data storage service
    - UNKNOWN: Cannot determine role
    
    Args:
        service_path: Full path to the service directory
        service_name: Name of the service directory
        
    Returns:
        String describing the architectural role
    """
    try:
        # Indicators for different architecture types
        has_routes = False
        has_ui_components = False
        has_api_handlers = False
        has_pages = False
        
        # Walk through the service directory (limit depth to avoid performance issues)
        for root, dirs, files in os.walk(service_path):
            # Limit depth to 3 levels
            depth = root[len(service_path):].count(os.sep)
            if depth > 3:
                continue
            
            # Check directory names for architectural indicators
            dir_names = [d.lower() for d in dirs]
            if 'routes' in dir_names or 'routing' in dir_names:
                has_routes = True
            if 'components' in dir_names or 'pages' in dir_names or 'app' in dir_names:
                has_ui_components = True
                if 'pages' in dir_names:
                    has_pages = True
            if 'handlers' in dir_names or 'api' in dir_names or 'controllers' in dir_names:
                has_api_handlers = True
            
            # Check file contents for routing patterns
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.go')):
                    file_path = os.path.join(root, file)
                    try:
                        # Read first 50 lines to check for routing patterns
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = ''.join([f.readline() for _ in range(50)])
                            content_lower = content.lower()
                            
                            # Check for routing indicators
                            if any(pattern in content_lower for pattern in [
                                'app.include_router', '@app.get', '@app.post', 
                                'router.get', 'router.post', 'app.route',
                                'http.handlefunc', 'mux.handlefunc'
                            ]):
                                has_routes = True
                            
                            # Check for UI framework patterns
                            if any(pattern in content_lower for pattern in [
                                'import react', 'from react', 'import vue',
                                'import { component }', 'export default function',
                                'import next', 'use client', 'use server'
                            ]):
                                has_ui_components = True
                                
                    except Exception:
                        pass  # Skip files that can't be read
        
        # Classify based on detected patterns
        if has_ui_components or has_pages:
            return "FRONTEND_APPLICATION"
        elif has_routes and has_api_handlers:
            return "REST_API_GATEWAY"
        elif has_routes or has_api_handlers:
            return "MICROSERVICE_BACKEND"
        elif 'database' in service_name.lower() or 'db' in service_name.lower():
            return "DATA_LAYER"
        else:
            return "UNKNOWN"
            
    except Exception as e:
        logger.debug(f"Error classifying service architecture for {service_name}: {e}")
        return "UNKNOWN"


def _generate_architecture_summary(
    service_architectures: Dict[str, str], 
    all_services: Set[str]
) -> str:
    """
    Generates a natural-language summary of the repository architecture.
    
    Creates a human-readable description of how services are organized and
    what architectural patterns are present in the repository.
    
    Args:
        service_architectures: Mapping of service names to their architectural roles
        all_services: Set of all detected service names
        
    Returns:
        Natural-language architecture summary string
    """
    if not service_architectures:
        # Fallback for when no services are detected or classified
        if all_services:
            return f"Detected {len(all_services)} service(s) with unclassified architecture."
        return "No services detected in repository structure."
    
    # Count services by architecture type
    arch_counts = {}
    for arch_role in service_architectures.values():
        arch_counts[arch_role] = arch_counts.get(arch_role, 0) + 1
    
    # Build summary components
    summary_parts = []
    
    # Determine overall architecture pattern
    if len(service_architectures) == 1:
        service_name = list(service_architectures.keys())[0]
        arch_role = service_architectures[service_name]
        if arch_role == "FRONTEND_APPLICATION":
            summary_parts.append(f"Single-service frontend application in '{service_name}' folder")
        elif arch_role == "MICROSERVICE_BACKEND":
            summary_parts.append(f"Single-service backend in '{service_name}' folder")
        else:
            summary_parts.append(f"Single-service architecture with '{service_name}' as {arch_role.lower().replace('_', ' ')}")
    else:
        summary_parts.append(f"Multi-service architecture with {len(service_architectures)} classified services")
    
    # Describe frontend services
    frontend_services = [name for name, role in service_architectures.items() 
                        if role == "FRONTEND_APPLICATION"]
    if frontend_services:
        if len(frontend_services) == 1:
            summary_parts.append(f"the '{frontend_services[0]}' folder serves the user interface")
        else:
            frontend_list = ', '.join(f"'{s}'" for s in frontend_services)
            summary_parts.append(f"frontend layers in {frontend_list}")
    
    # Describe backend services
    backend_services = [name for name, role in service_architectures.items() 
                       if role in ["REST_API_GATEWAY", "MICROSERVICE_BACKEND"]]
    if backend_services:
        if len(backend_services) == 1:
            summary_parts.append(f"the '{backend_services[0]}' folder handles routing and API functions")
        else:
            backend_list = ', '.join(f"'{s}'" for s in backend_services)
            summary_parts.append(f"backend services in {backend_list} handle API routing")
    
    # Describe data layer
    data_services = [name for name, role in service_architectures.items() 
                    if role == "DATA_LAYER"]
    if data_services:
        data_list = ', '.join(f"'{s}'" for s in data_services)
        summary_parts.append(f"data persistence in {data_list}")
    
    # Mention unclassified services if any
    unclassified = [name for name, role in service_architectures.items() 
                   if role == "UNKNOWN"]
    if unclassified and len(unclassified) < len(service_architectures):
        summary_parts.append(f"{len(unclassified)} additional service(s) with unclassified roles")
    
    # Join parts into coherent summary
    if len(summary_parts) == 1:
        return f"Detected a {summary_parts[0]}."
    elif len(summary_parts) == 2:
        return f"Detected a {summary_parts[0]}, where {summary_parts[1]}."
    else:
        main_part = summary_parts[0]
        detail_parts = ", ".join(summary_parts[1:-1])
        last_part = summary_parts[-1]
        return f"Detected a {main_part}, where {detail_parts}, and {last_part}."


def _get_fallback_data() -> Dict[str, Any]:
    """
    Provides standard fallback data when repository analysis fails.
    
    This ensures the LangGraph workflow can continue even if the
    repository analysis encounters errors or corrupted files.
    
    Returns:
        Dictionary with safe default values for services, languages, and frameworks
    """
    return {
        "services": ["unknown-service"],
        "languages": ["unknown"],
        "frameworks": ["unknown"],
    }

# Made with Bob
