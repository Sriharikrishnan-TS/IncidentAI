"""
Repository Memory Storage Layer
Handles persistence of repository analysis data to the database.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)

# Global flag to track if database is available
DATABASE_AVAILABLE = False
DB_CLIENT = None

# Try to import database client - fail gracefully if not available
try:
    # TODO: Replace with actual database client (PostgreSQL, MongoDB, etc.)
    # For now, we'll use a mock storage layer
    from memory.storage_adapter import StorageAdapter
    DB_CLIENT = StorageAdapter()
    DATABASE_AVAILABLE = True
    logger.info("Database client successfully initialized")
except Exception as e:
    logger.warning(f"Database client initialization failed, using mock storage: {e}")
    DATABASE_AVAILABLE = False


class RepositoryMemory:
    """
    Repository Memory Layer for persisting repository analysis data.
    
    This class handles storing and retrieving repository metadata,
    including services, languages, frameworks, and imports.
    """
    
    def __init__(self):
        """Initialize the repository memory layer."""
        self.client = DB_CLIENT
        self.use_mock = not DATABASE_AVAILABLE
        self.mock_storage: Dict[str, Dict[str, Any]] = {}
        
        if self.use_mock:
            logger.info("Using mock storage layer for repository memory")
    
    def store_repository_analysis(
        self,
        repo_id: str,
        repo_path: str,
        services: list,
        languages: list,
        frameworks: list,
        imports: Optional[list] = None
    ) -> bool:
        """
        Stores repository analysis results to the database.
        
        Args:
            repo_id: Unique identifier for the repository
            repo_path: Path to the repository
            services: List of detected services
            languages: List of detected programming languages
            frameworks: List of detected frameworks
            imports: Optional list of detected imports
            
        Returns:
            True if storage was successful, False otherwise
        """
        try:
            # Create summary text block
            summary = self._create_summary_text(
                repo_id, repo_path, services, languages, frameworks, imports
            )
            
            # Create payload for storage
            payload = {
                "repo_id": repo_id,
                "repo_path": repo_path,
                "services": services,
                "languages": languages,
                "frameworks": frameworks,
                "imports": imports or [],
                "summary": summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_version": "1.0.0"
            }
            
            logger.info(f"Storing repository analysis for repo_id={repo_id}")
            logger.debug(f"Summary: {summary}")
            
            # Store using appropriate method
            if self.use_mock:
                return self._store_mock(repo_id, payload)
            else:
                return self._store_database(repo_id, payload)
                
        except Exception as e:
            logger.error(f"Error storing repository analysis for {repo_id}: {e}", exc_info=True)
            return False
    
    def _create_summary_text(
        self,
        repo_id: str,
        repo_path: str,
        services: list,
        languages: list,
        frameworks: list,
        imports: Optional[list] = None
    ) -> str:
        """
        Creates a clean text summary of repository assets.
        
        Args:
            repo_id: Repository identifier
            repo_path: Repository path
            services: List of services
            languages: List of languages
            frameworks: List of frameworks
            imports: Optional list of imports
            
        Returns:
            Formatted summary text
        """
        summary_lines = [
            f"Repository Analysis Summary",
            f"=" * 50,
            f"Repository ID: {repo_id}",
            f"Repository Path: {repo_path}",
            f"",
            f"Services ({len(services)}):",
        ]
        
        if services:
            for service in services:
                summary_lines.append(f"  - {service}")
        else:
            summary_lines.append("  - No services detected")
        
        summary_lines.append("")
        summary_lines.append(f"Languages ({len(languages)}):")
        if languages:
            summary_lines.append(f"  {', '.join(languages)}")
        else:
            summary_lines.append("  - No languages detected")
        
        summary_lines.append("")
        summary_lines.append(f"Frameworks ({len(frameworks)}):")
        if frameworks:
            for framework in frameworks:
                summary_lines.append(f"  - {framework}")
        else:
            summary_lines.append("  - No frameworks detected")
        
        if imports:
            summary_lines.append("")
            summary_lines.append(f"Top Imports ({min(10, len(imports))}):")
            for imp in imports[:10]:
                summary_lines.append(f"  - {imp}")
            if len(imports) > 10:
                summary_lines.append(f"  ... and {len(imports) - 10} more")
        
        summary_lines.append("")
        summary_lines.append(f"Analysis completed at: {datetime.now(timezone.utc).isoformat()}")
        summary_lines.append("=" * 50)
        
        return "\n".join(summary_lines)
    
    def _store_mock(self, repo_id: str, payload: Dict[str, Any]) -> bool:
        """
        Stores data in mock in-memory storage.
        
        Args:
            repo_id: Repository identifier
            payload: Data to store
            
        Returns:
            True if successful
        """
        try:
            self.mock_storage[repo_id] = payload
            logger.info(f"Successfully stored repository analysis in mock storage for {repo_id}")
            return True
        except Exception as e:
            logger.error(f"Mock storage error: {e}")
            return False
    
    def _store_database(self, repo_id: str, payload: Dict[str, Any]) -> bool:
        """
        Stores data in actual database.
        
        Args:
            repo_id: Repository identifier
            payload: Data to store
            
        Returns:
            True if successful
        """
        try:
            if self.client:
                self.client.store("repository_analysis", repo_id, payload)
                logger.info(f"Successfully stored repository analysis in database for {repo_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Database storage error: {e}")
            return False
    
    def retrieve_repository_analysis(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves repository analysis from storage.
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            Stored analysis data or None if not found
        """
        try:
            if self.use_mock:
                return self.mock_storage.get(repo_id)
            elif self.client:
                return self.client.retrieve("repository_analysis", repo_id)
            return None
        except Exception as e:
            logger.error(f"Error retrieving repository analysis for {repo_id}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Returns statistics about stored repository analyses.
        
        Returns:
            Dictionary with storage statistics
        """
        if self.use_mock:
            return {
                "storage_type": "mock",
                "total_repositories": len(self.mock_storage),
                "repository_ids": list(self.mock_storage.keys())
            }
        elif self.client:
            return {
                "storage_type": "database",
                "status": "connected"
            }
        return {
            "storage_type": "none",
            "status": "unavailable"
        }


# Global instance for easy access
_repository_memory_instance = None


def get_repository_memory() -> RepositoryMemory:
    """
    Returns the global RepositoryMemory instance (singleton pattern).
    
    Returns:
        RepositoryMemory instance
    """
    global _repository_memory_instance
    if _repository_memory_instance is None:
        _repository_memory_instance = RepositoryMemory()
    return _repository_memory_instance

# Made with Bob
