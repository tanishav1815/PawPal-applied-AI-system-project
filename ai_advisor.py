"""
PawPal+ AI Advisor — RAG-powered care advisor using the Gemini API.

Components:
  RAGRetriever  — loads .md files from knowledge_base/, retrieves chunks using semantic
                  embeddings (text-embedding-004). Falls back to keyword overlap when no
                  API key is provided (used by tests).
  PawPalAdvisor — retrieves context, calls Gemini, logs every interaction.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

load_dotenv()

from pawpal_system import Pet, Task

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("pawpal")
if not logger.handlers:
    _handler = logging.FileHandler("pawpal.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge_base"
CACHE_FILE = KNOWLEDGE_DIR / ".embeddings_cache.json"


# ---------------------------------------------------------------------------
# RAG Retriever
# ---------------------------------------------------------------------------

class RAGRetriever:
    """
    Loads markdown files from knowledge_base/ into paragraph-level chunks.

    When an API key is provided, chunks and queries are embedded using
    text-embedding-004 and retrieved by cosine similarity — so synonyms
    and paraphrases match correctly.

    When no API key is provided (e.g. in tests), falls back to keyword
    overlap scoring.

    Embeddings are cached to disk so they are only computed once.
    """

    EMBEDDING_MODEL = "text-embedding-004"

    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR, api_key: Optional[str] = None):
        self._chunks: list[dict] = []
        self._embeddings: list[list[float]] = []
        self._client: Optional[genai.Client] = None
        self._use_embeddings = False
        self._load(knowledge_dir)
        if api_key and self._chunks:
            self._client = genai.Client(api_key=api_key)
            self._build_embeddings()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self, directory: Path) -> None:
        if not directory.exists():
            logger.warning("Knowledge directory not found: %s", directory)
            return
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for para in re.split(r"\n{2,}", text):
                para = para.strip()
                if len(para) > 40:
                    self._chunks.append({"text": para, "source": path.name})
        logger.info("RAG loaded %d chunks from %d files",
                    len(self._chunks), len(list(directory.glob("*.md"))))

    # ------------------------------------------------------------------
    # Embedding (with disk cache)
    # ------------------------------------------------------------------

    def _build_embeddings(self) -> None:
        cache: dict = {}
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                cache = {}

        all_embeddings: list[list[float]] = []
        new_entries: dict = {}

        for chunk in self._chunks:
            key = hashlib.md5(chunk["text"].encode()).hexdigest()
            if key in cache:
                all_embeddings.append(cache[key])
            else:
                try:
                    resp = self._client.models.embed_content(
                        model=self.EMBEDDING_MODEL,
                        contents=chunk["text"],
                    )
                    emb = list(resp.embeddings[0].values)
                    all_embeddings.append(emb)
                    new_entries[key] = emb
                except Exception as e:
                    logger.warning("Embedding failed for chunk, using zero vector: %s", e)
                    all_embeddings.append([])

        if new_entries:
            cache.update(new_entries)
            try:
                CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
            except Exception as e:
                logger.warning("Could not write embedding cache: %s", e)

        self._embeddings = all_embeddings
        self._use_embeddings = True
        logger.info("Embeddings ready: %d chunks (%d from cache, %d new)",
                    len(self._chunks), len(self._chunks) - len(new_entries), len(new_entries))

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

    @staticmethod
    def _keyword_score(chunk_text: str, query: str) -> float:
        chunk_words = set(re.findall(r"\w+", chunk_text.lower()))
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return 0.0
        return len(chunk_words & query_words) / len(query_words)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Return the top_k most relevant chunks, using semantic search when possible."""
        if self._use_embeddings and self._client:
            try:
                resp = self._client.models.embed_content(
                    model=self.EMBEDDING_MODEL,
                    contents=query,
                )
                query_emb = list(resp.embeddings[0].values)
                ranked = sorted(
                    range(len(self._chunks)),
                    key=lambda i: self._cosine_similarity(query_emb, self._embeddings[i]),
                    reverse=True,
                )
                return [self._chunks[i] for i in ranked[:top_k]]
            except Exception as e:
                logger.warning("Semantic retrieval failed, falling back to keyword: %s", e)

        # Keyword fallback (used by tests and when API key is absent)
        ranked = sorted(
            self._chunks,
            key=lambda c: self._keyword_score(c["text"], query),
            reverse=True,
        )
        return ranked[:top_k]

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


# ---------------------------------------------------------------------------
# PawPal AI Advisor
# ---------------------------------------------------------------------------

class PawPalAdvisor:
    """
    Answers pet care questions grounded in retrieved knowledge + the pet's live schedule.

    Usage:
        advisor = PawPalAdvisor()
        result  = advisor.advise("Is Mochi getting enough exercise?", pet, plan)
        print(result["response"])
        print(result["sources"])
    """

    MODEL = "gemini-2.5-flash"

    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR):
        api_key = os.getenv("GEMINI_API_KEY")
        self._retriever = RAGRetriever(knowledge_dir, api_key=api_key)
        self._client = genai.Client(api_key=api_key)

    def advise(
        self,
        question: str,
        pet: Pet,
        scheduled_tasks: Optional[list[Task]] = None,
    ) -> dict:
        """
        Returns:
            response  — AI answer (empty string on error)
            sources   — sorted list of knowledge file names used
            error     — error message string, or None on success
        """
        scheduled_tasks = scheduled_tasks or []

        chunks = self._retriever.retrieve(question, top_k=3)
        context_text = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
        sources = sorted({c["source"] for c in chunks})

        task_lines = (
            "\n".join(
                f"- {t.title} ({t.duration_minutes} min, {t.priority} priority, {t.category})"
                for t in scheduled_tasks
            )
            if scheduled_tasks else "No tasks scheduled yet."
        )

        system_prompt = (
            "You are PawPal AI, a knowledgeable and friendly pet care advisor. "
            "Answer questions about a specific pet's care using the retrieved knowledge "
            "and the pet's current schedule provided below. "
            "Be concise, practical, and warm. "
            "If the retrieved knowledge does not cover the question, say so honestly "
            "rather than guessing."
        )

        user_message = (
            f"Pet profile:\n"
            f"- Name: {pet.name}\n"
            f"- Species: {pet.species}\n"
            f"- Age: {pet.age} year(s)\n"
            f"- Special needs: {', '.join(pet.special_needs) if pet.special_needs else 'none'}\n"
            f"\nToday's scheduled tasks:\n{task_lines}\n"
            f"\nRelevant care knowledge:\n{context_text}\n"
            f"\nQuestion: {question}"
        )

        logger.info("AI query | pet=%s species=%s age=%d question=%r sources=%s",
                    pet.name, pet.species, pet.age, question, sources)

        try:
            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=user_message,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=512,
                ),
            )
            response_text = response.text
            logger.info("AI response | pet=%s chars=%d", pet.name, len(response_text))
            return {"response": response_text, "sources": sources, "error": None}

        except Exception as e:
            msg = str(e)
            if "api key" in msg.lower() or "api_key" in msg.lower() or "permission" in msg.lower():
                msg = "GEMINI_API_KEY is missing or invalid. Set it in your .env file."
            logger.error("AI error: %s", msg)
            return {"response": "", "sources": [], "error": msg}
