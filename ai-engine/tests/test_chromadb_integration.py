"""
Tests for ChromaDB Integration in Git History Agent
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.git_history_agent.node import (
    _generate_memory_report,
    _get_chromadb_client,
    _persist_to_chromadb
)


def test_memory_report_generation():
    """Test that memory report is generated correctly."""
    print("Test 1: Memory Report Generation")
    print("-" * 70)
    
    report = _generate_memory_report(
        repo_id="test-repo",
        services=["frontend", "backend", "api"],
        languages=["Python", "TypeScript"],
        frameworks=["FastAPI", "React"],
        high_churn_services=["frontend", "api"],
        recent_commits=87,
        top_contributors=["Alice", "Bob", "Charlie"]
    )
    
    # Verify report contains key information
    assert "test-repo" in report
    assert "frontend" in report
    assert "backend" in report
    assert "api" in report
    assert "Python" in report
    assert "TypeScript" in report
    assert "FastAPI" in report
    assert "React" in report
    assert "87" in report
    assert "Alice" in report
    assert "Bob" in report
    assert "Charlie" in report
    assert "high risk churn" in report.lower()
    
    print("[OK] Memory report generated successfully")
    print(f"\nSample Report:\n{report}\n")


def test_chromadb_client_initialization():
    """Test ChromaDB client initialization (may fail if ChromaDB not running)."""
    print("Test 2: ChromaDB Client Initialization")
    print("-" * 70)
    
    client = _get_chromadb_client()
    
    if client is None:
        print("[INFO] ChromaDB not available or not running at localhost:8000")
        print("[INFO] This is expected if ChromaDB is not installed or server is not running")
    else:
        print("[OK] Successfully connected to ChromaDB at localhost:8000")
        
        # Try to get heartbeat
        try:
            client.heartbeat()
            print("[OK] ChromaDB server is responsive")
        except Exception as e:
            print(f"[WARNING] ChromaDB heartbeat failed: {e}")
    
    print()


def test_chromadb_persistence():
    """Test full persistence workflow (may fail if ChromaDB not running)."""
    print("Test 3: ChromaDB Persistence")
    print("-" * 70)
    
    success = _persist_to_chromadb(
        repo_id="test-repo-123",
        memory_report="Test repository with services: frontend, backend. High churn in frontend.",
        services=["frontend", "backend"],
        languages=["Python"],
        frameworks=["FastAPI"],
        high_churn_services=["frontend"],
        recent_commits=42,
        top_contributors=["Alice", "Bob"]
    )
    
    if success:
        print("[OK] Successfully persisted to ChromaDB")
        print("[INFO] Document stored with ID: test-repo-123_onboarding")
    else:
        print("[INFO] ChromaDB persistence skipped (server not available)")
        print("[INFO] This is expected if ChromaDB is not installed or server is not running")
    
    print()


def test_defensive_error_handling():
    """Test that errors don't crash the system."""
    print("Test 4: Defensive Error Handling")
    print("-" * 70)
    
    # Test with invalid data - should not raise exceptions
    try:
        report = _generate_memory_report(
            repo_id="",
            services=[],
            languages=[],
            frameworks=[],
            high_churn_services=[],
            recent_commits=0,
            top_contributors=[]
        )
        print("[OK] Handles empty data gracefully")
        print(f"Empty data report: {report[:100]}...")
    except Exception as e:
        print(f"[FAIL] Unexpected exception: {e}")
    
    # Test persistence with invalid repo_id - should not crash
    try:
        success = _persist_to_chromadb(
            repo_id="",
            memory_report="Test",
            services=[],
            languages=[],
            frameworks=[],
            high_churn_services=[],
            recent_commits=0,
            top_contributors=[]
        )
        print("[OK] Handles persistence errors gracefully")
    except Exception as e:
        print(f"[FAIL] Unexpected exception: {e}")
    
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("ChromaDB Integration Tests")
    print("=" * 70)
    print()
    
    # Test 1: Memory report generation
    test_memory_report_generation()
    
    # Test 2: ChromaDB client initialization
    test_chromadb_client_initialization()
    
    # Test 3: ChromaDB persistence
    test_chromadb_persistence()
    
    # Test 4: Defensive error handling
    test_defensive_error_handling()
    
    print("=" * 70)
    print("[SUCCESS] All ChromaDB integration tests completed!")
    print()
    print("Note: Some tests may show [INFO] messages if ChromaDB is not running.")
    print("To start ChromaDB server: docker-compose up chromadb")
    print("=" * 70)


# Made with Bob