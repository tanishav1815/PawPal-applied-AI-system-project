"""
Tests for PawPal+ AI Advisor — RAGRetriever only (no API key required).
Run with: python -m pytest
"""

from pathlib import Path

import pytest

from ai_advisor import RAGRetriever
from pawpal_system import Owner, Pet, Task, Scheduler

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge_base"


# ---------------------------------------------------------------------------
# RAGRetriever — loading
# ---------------------------------------------------------------------------

def test_retriever_loads_chunks():
    """RAGRetriever should load at least one chunk from the knowledge base."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    assert retriever.chunk_count > 0


def test_retriever_loads_multiple_files():
    """RAGRetriever should load chunks from more than one file."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    sources = {c["source"] for c in retriever.retrieve("dog cat exercise feed groom", top_k=20)}
    assert len(sources) > 1


def test_retriever_missing_dir_does_not_crash():
    """RAGRetriever should handle a missing knowledge directory gracefully."""
    retriever = RAGRetriever(Path("/nonexistent/path"))
    assert retriever.chunk_count == 0


# ---------------------------------------------------------------------------
# RAGRetriever — retrieval relevance
# ---------------------------------------------------------------------------

def test_retrieve_exercise_query_returns_exercise_content():
    """A query about dog exercise should return chunks from dogs_exercise.md."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("How much exercise does my dog need daily?", top_k=3)
    sources = [r["source"] for r in results]
    assert "dogs_exercise.md" in sources


def test_retrieve_grooming_query_returns_grooming_content():
    """A grooming question should return chunks from grooming.md."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("How often should I brush and groom my dog's coat?", top_k=3)
    sources = [r["source"] for r in results]
    assert "grooming.md" in sources


def test_retrieve_senior_query_returns_senior_content():
    """A query about a senior pet should surface senior_pets.md chunks."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("My dog is 8 years old. Is she considered senior?", top_k=3)
    sources = [r["source"] for r in results]
    assert "senior_pets.md" in sources


def test_retrieve_medication_query_returns_medication_content():
    """A query about medication should return chunks from medications.md."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("How do I remember to give my cat her daily medication?", top_k=3)
    sources = [r["source"] for r in results]
    assert "medications.md" in sources


def test_retrieve_enrichment_query_returns_enrichment_content():
    """A query about enrichment should return chunks from enrichment.md."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("What mental enrichment activities can I do with my dog?", top_k=3)
    sources = [r["source"] for r in results]
    assert "enrichment.md" in sources


def test_retrieve_returns_top_k_results():
    """retrieve(top_k=N) should return exactly N results when enough chunks exist."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("exercise walk feed groom", top_k=5)
    assert len(results) == 5


def test_retrieve_empty_query_does_not_crash():
    """An empty query string should not raise an exception."""
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    results = retriever.retrieve("", top_k=3)
    assert isinstance(results, list)


# ---------------------------------------------------------------------------
# RAG context differs by species (proves RAG influences the answer)
# ---------------------------------------------------------------------------

def test_dog_query_differs_from_cat_query():
    """
    Retrieving context for a dog exercise query vs a cat care query should
    produce different source sets, proving species-specific retrieval.
    """
    retriever = RAGRetriever(KNOWLEDGE_DIR)
    dog_sources = {r["source"] for r in retriever.retrieve(
        "How much daily exercise does my dog need?", top_k=3
    )}
    cat_sources = {r["source"] for r in retriever.retrieve(
        "How should I care for my indoor cat's daily needs?", top_k=3
    )}
    assert dog_sources != cat_sources
