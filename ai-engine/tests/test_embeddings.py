"""
Test suite for embedding generation and ChromaDB persistence.

Tests the vector embedding functionality for the Engineering Memory Layer.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.embeddings import (
    generate_embeddings,
    generate_batch_embeddings,
    get_embedding_dimension,
    is_using_sentence_transformers,
    _generate_fallback_embedding
)


def test_generate_embeddings_basic():
    """Test basic embedding generation."""
    text = "This is a test repository with Python and FastAPI frameworks."
    
    embedding = generate_embeddings(text)
    
    assert isinstance(embedding, list), "Embedding should be a list"
    assert len(embedding) > 0, "Embedding should not be empty"
    assert all(isinstance(x, float) for x in embedding), "All embedding values should be floats"
    
    # Check dimensionality
    expected_dim = get_embedding_dimension()
    assert len(embedding) == expected_dim, f"Embedding should have {expected_dim} dimensions"
    
    print(f"[PASS] Basic embedding generation test passed")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  Using sentence-transformers: {is_using_sentence_transformers()}")


def test_generate_embeddings_consistency():
    """Test that identical text produces identical embeddings."""
    text = "Repository analysis for IncidentOS project"
    
    embedding1 = generate_embeddings(text)
    embedding2 = generate_embeddings(text)
    
    assert embedding1 == embedding2, "Identical text should produce identical embeddings"
    
    print("[PASS] Embedding consistency test passed")


def test_generate_embeddings_different_texts():
    """Test that different texts produce different embeddings."""
    text1 = "Frontend application with React and Next.js"
    text2 = "Backend service with Go and Gin framework"
    
    embedding1 = generate_embeddings(text1)
    embedding2 = generate_embeddings(text2)
    
    assert embedding1 != embedding2, "Different texts should produce different embeddings"
    
    print("[PASS] Different texts produce different embeddings test passed")


def test_generate_batch_embeddings():
    """Test batch embedding generation."""
    texts = [
        "Repository contains frontend service",
        "Backend API with high churn",
        "Database layer with PostgreSQL"
    ]
    
    embeddings = generate_batch_embeddings(texts)
    
    assert len(embeddings) == len(texts), "Should generate one embedding per text"
    assert all(isinstance(emb, list) for emb in embeddings), "All embeddings should be lists"
    
    expected_dim = get_embedding_dimension()
    assert all(len(emb) == expected_dim for emb in embeddings), \
        f"All embeddings should have {expected_dim} dimensions"
    
    print(f"[PASS] Batch embedding generation test passed")
    print(f"  Generated {len(embeddings)} embeddings")


def test_empty_text_handling():
    """Test handling of empty or whitespace-only text."""
    empty_texts = ["", "   ", "\n\t"]
    
    for text in empty_texts:
        embedding = generate_embeddings(text)
        assert isinstance(embedding, list), "Should return a list even for empty text"
        assert len(embedding) == get_embedding_dimension(), "Should return correct dimension"
    
    print("[PASS] Empty text handling test passed")


def test_fallback_embedding():
    """Test the fallback embedding generation."""
    text = "Test repository summary"
    
    embedding = _generate_fallback_embedding(text, dimensions=128)
    
    assert len(embedding) == 128, "Fallback should generate 128-dimensional embedding"
    assert all(isinstance(x, float) for x in embedding), "All values should be floats"
    assert all(-1.0 <= x <= 1.0 for x in embedding), "All values should be in [-1, 1] range"
    
    # Test consistency
    embedding2 = _generate_fallback_embedding(text, dimensions=128)
    assert embedding == embedding2, "Fallback should be deterministic"
    
    print("[PASS] Fallback embedding test passed")


def test_embedding_for_repository_summaries():
    """Test embedding generation for typical repository summaries."""
    summaries = [
        "Repository IncidentOS contains services: frontend, backend-go, ai-engine. "
        "The codebase uses Python, Go, TypeScript with frameworks: FastAPI, Gin, Next.js. "
        "Analysis of the last 42 commits shows that high risk churn is isolated to: frontend, backend-go.",
        
        "Detected a Multi-service architecture with 3 classified services, where the 'frontend' "
        "folder serves the user interface, and the 'backend-go' folder handles routing and API functions.",
        
        "Repository IncidentOS PR and branch activity analysis: 15 merge commits detected. "
        "Services with high PR activity: frontend, backend-go, ai-engine. Active branches: 1. "
        "PR to commit ratio: 24.00%."
    ]
    
    embeddings = generate_batch_embeddings(summaries)
    
    assert len(embeddings) == 3, "Should generate 3 embeddings"
    
    # Verify all embeddings are different (they describe different aspects)
    assert embeddings[0] != embeddings[1], "Different summaries should have different embeddings"
    assert embeddings[1] != embeddings[2], "Different summaries should have different embeddings"
    assert embeddings[0] != embeddings[2], "Different summaries should have different embeddings"
    
    print("[PASS] Repository summary embedding test passed")
    print(f"  Generated embeddings for {len(summaries)} different summary types")


def test_embedding_metadata_compatibility():
    """Test that embeddings work with ChromaDB metadata structure."""
    # Simulate the metadata structure used in ChromaDB persistence
    repo_summaries = {
        "onboarding_summary": "Repository analysis with services and frameworks",
        "architecture_summary": "Multi-service architecture with frontend and backend",
        "pr_analytics": "High PR activity in frontend service with 15 merge commits"
    }
    
    embeddings = {}
    for doc_type, text in repo_summaries.items():
        embedding = generate_embeddings(text)
        embeddings[doc_type] = embedding
        
        # Verify embedding is valid
        assert len(embedding) == get_embedding_dimension()
        assert all(isinstance(x, float) for x in embedding)
    
    print("[PASS] Embedding metadata compatibility test passed")
    print(f"  Generated embeddings for {len(embeddings)} document types")


def run_all_tests():
    """Run all embedding tests."""
    print("\n" + "="*70)
    print("Running Embedding Generation Tests")
    print("="*70 + "\n")
    
    try:
        test_generate_embeddings_basic()
        test_generate_embeddings_consistency()
        test_generate_embeddings_different_texts()
        test_generate_batch_embeddings()
        test_empty_text_handling()
        test_fallback_embedding()
        test_embedding_for_repository_summaries()
        test_embedding_metadata_compatibility()
        
        print("\n" + "="*70)
        print("[SUCCESS] All embedding tests passed!")
        print("="*70 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
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
