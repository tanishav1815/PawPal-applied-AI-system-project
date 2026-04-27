# PawPal+ AI Model Card

## Model Details

- **Model used:** Gemini 2.5 Flash (`gemini-2.5-flash`) via the Google Gemini API (`google-genai` SDK)
- **Embedding model:** `text-embedding-004` via the Google Gemini API (used for semantic RAG retrieval)
- **AI feature:** Retrieval-Augmented Generation (RAG)
- **Retrieval method:** Semantic embeddings (cosine similarity); keyword overlap fallback when no API key is present (used by tests)
- **Knowledge base:** 7 hand-authored markdown files covering dog exercise, cat care, senior pet care, nutrition, grooming, medications, and enrichment

---

## Limitations and Biases

**Coverage bias:** The knowledge base was written by hand and covers only common domestic pets (dogs and cats) across general categories. It does not cover exotic pets, breed-specific health conditions, or regional veterinary guidelines. A user with a rabbit, ferret, or reptile will receive generic or off-topic retrieved context.

**Retrieval limitations:** Even with semantic embeddings, retrieval quality depends on the knowledge base containing relevant content. If a user's question is about a topic not covered in the 7 knowledge files (e.g., a rare breed condition or a specific medication brand), the retriever will return the closest available chunk, which may not be relevant. Gemini is instructed to say so honestly rather than guess.

**Model knowledge cutoff:** Gemini's training data has a knowledge cutoff, so advice about very new medications, recently updated veterinary guidelines, or newly identified health conditions may be absent or outdated.

**Not a substitute for a vet:** All AI-generated advice in PawPal+ is informational. The system explicitly does not diagnose conditions, recommend specific medications, or replace professional veterinary care. High-stakes decisions (surgery, medication changes, emergency symptoms) must involve a licensed veterinarian.

**Single-pet context:** The AI advisor is scoped to one pet at a time. If an owner has two pets with conflicting needs (e.g., a high-energy dog and a senior cat), the system will not reason about trade-offs between them.

---

## Potential Misuse and Safeguards

**Potential misuse:** A user could describe a sick pet and ask the AI for a diagnosis or treatment. The AI might generate a plausible-sounding but incorrect response, potentially delaying real veterinary care.

**Safeguards in place:**
- The system prompt instructs Gemini to be honest when the knowledge base does not cover a topic, rather than guessing.
- All AI interactions are logged to `pawpal.log` with timestamps, pet context, and response lengths.
- Error handling catches authentication failures, connection errors, and unexpected exceptions, displaying a user-facing error message rather than crashing.
- The UI caption reads "Ask a question about your pet's care" — framing the advisor as a care planning tool, not a diagnostic tool.

**Additional safeguard recommended for production:** Add a disclaimer banner to the AI section stating "This is not veterinary advice."

---

## Testing Surprises

**Retrieval failure before knowledge base rewrite:** The most significant surprise during testing was a retrieval quality failure. The query "Is Mochi getting enough exercise?" initially produced this AI response: *"Our current knowledge doesn't specify the exact ideal amount of exercise for a 3-year-old dog."* The root cause: the adult-dog paragraph in `dogs_exercise.md` was written without the word "exercise" (using "physical activity" and "movement" instead), so the keyword overlap retriever scored the Types-of-Exercise paragraph higher. This was fixed in two steps: (1) rewrote the paragraph to include exact query vocabulary, and (2) upgraded the retriever to semantic embeddings so vocabulary mismatches no longer cause retrieval failures.

**Semantic embeddings on a small knowledge base:** After upgrading to `text-embedding-004`, both keyword overlap and semantic retrieval scored identically on the production knowledge base. This is because the knowledge base rewrite (Step 1) already aligned vocabulary well enough for keyword overlap to work. The semantic upgrade is the correct architectural decision for robustness at scale — it handles synonyms, paraphrases, and vocabulary drift that keyword overlap cannot — but on a carefully written 7-file knowledge base, both methods perform equally.

**Species-specific retrieval:** Species-specific queries (dog vs. cat) reliably pulled different source sets, which is the core requirement for proving that RAG meaningfully changes the AI's response rather than just appending boilerplate context. The `test_dog_query_differs_from_cat_query` test was added specifically to document this property.

---

## AI Collaboration

This project was built with assistance from Claude Code (Anthropic's AI coding assistant). The following captures honest examples of where the collaboration worked well and where it required correction. Note: "Claude" below refers to Claude Code, the development tool — not the deployed model, which is Gemini.

**Helpful suggestion:** When the retriever was failing on "Is Mochi getting enough exercise?", Claude Code diagnosed the root cause (vocabulary mismatch between query and knowledge base paragraph) and proposed the two-step fix: rewrite the paragraph AND upgrade to semantic embeddings. The two-step approach was the right call — it both fixed the immediate bug and improved the architectural robustness of the system.

**Helpful suggestion:** Claude Code recommended caching embeddings to disk using an MD5-keyed JSON file (`knowledge_base/.embeddings_cache.json`). This means the ~70 chunk embeddings are computed only once. On subsequent app runs, the cache loads in milliseconds rather than making 70 API calls. This was a practical improvement that significantly reduces startup time and API costs.

**Flawed suggestion:** Claude Code initially suggested using `re.split(r"\n", text)` (single newline) to split knowledge files into chunks. This would have created hundreds of single-line fragments — section headers, blank lines, and short phrases — none of which would be meaningful retrieval units. The correct approach was to split on double newlines (`\n{2,}`) to get full paragraphs, which are the natural unit of meaning in the knowledge files. The suggestion was caught before implementation by reasoning about what chunk granularity would actually serve the retriever well.
