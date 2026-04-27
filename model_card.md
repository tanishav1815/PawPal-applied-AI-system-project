# PawPal+ AI Model Card

## Model Details

- **Model used:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) via the Anthropic API
- **AI feature:** Retrieval-Augmented Generation (RAG)
- **Retrieval method:** Keyword overlap scoring (word intersection / query length)
- **Knowledge base:** 7 hand-authored markdown files covering dog exercise, cat care, senior pet care, nutrition, grooming, medications, and enrichment

---

## Limitations and Biases

**Coverage bias:** The knowledge base was written by hand and covers only common domestic pets (dogs and cats) across general categories. It does not cover exotic pets, breed-specific health conditions, or regional veterinary guidelines. A user with a rabbit, ferret, or reptile will receive generic or off-topic retrieved context.

**Retrieval limitations:** The current retriever uses simple word overlap scoring (TF-IDF-style), not semantic embeddings. This means queries using synonyms or phrasing that differs from the knowledge base vocabulary may retrieve low-relevance chunks. For example, asking "Is my pup active enough?" may not score as well as "Is my dog getting enough exercise?" because "pup" is not a term used in the knowledge files.

**Model knowledge cutoff:** Claude's training data has a knowledge cutoff, so advice about very new medications, recently updated veterinary guidelines, or newly identified health conditions may be absent or outdated.

**Not a substitute for a vet:** All AI-generated advice in PawPal+ is informational. The system explicitly does not diagnose conditions, recommend specific medications, or replace professional veterinary care. High-stakes decisions (surgery, medication changes, emergency symptoms) must involve a licensed veterinarian.

**Single-pet context:** The AI advisor is scoped to one pet at a time. If an owner has two pets with conflicting needs (e.g., a high-energy dog and a senior cat), the system will not reason about trade-offs between them.

---

## Potential Misuse and Safeguards

**Potential misuse:** A user could describe a sick pet and ask the AI for a diagnosis or treatment. The AI might generate a plausible-sounding but incorrect response, potentially delaying real veterinary care.

**Safeguards in place:**
- The system prompt instructs Claude to be honest when the knowledge base does not cover a topic, rather than guessing.
- All AI interactions are logged to `pawpal.log` with timestamps, pet context, and token counts.
- Error handling catches authentication failures, connection errors, and unexpected exceptions, displaying a user-facing error message rather than crashing.
- The UI caption reads "Ask a question about your pet's care" — framing the advisor as a care planning tool, not a diagnostic tool.

**Additional safeguard recommended for production:** Add a disclaimer banner to the AI section stating "This is not veterinary advice."

---

## Testing Surprises

The most surprising result during testing was how well the simple keyword-overlap retriever performed on specific queries without any embedding model. Asking "How often should I groom my dog's coat?" consistently retrieved `grooming.md` as the top source, and "My cat needs medication twice a day" reliably retrieved `medications.md`. The retriever only struggled on very short or vague queries (e.g., "help" or "is this enough") where there was insufficient vocabulary to differentiate between files.

A second surprise was that species-specific queries (dog vs. cat) reliably pulled different source sets, which is the core requirement for proving that RAG meaningfully changes the AI's response rather than just appending boilerplate context. The `test_dog_query_differs_from_cat_query` test was added specifically to document this property.

---

## AI Collaboration

**Helpful suggestion:** When designing the `RAGRetriever._score()` method, Claude suggested normalizing the overlap score by query length (intersection / |query_words|) rather than by chunk length. This was the right call: normalizing by query length rewards chunks that cover a large fraction of what the user asked, rather than rewarding very large chunks that happen to contain a few matching words by chance.

**Flawed suggestion:** Claude initially suggested using `re.split(r"\n", text)` (single newline) to split knowledge files into chunks. This would have created hundreds of single-line fragments — section headers, blank lines, and short phrases — none of which would be meaningful retrieval units. The correct approach was to split on double newlines (`\n{2,}`) to get full paragraphs, which are the natural unit of meaning in the knowledge files. The suggestion was caught before implementation by reasoning about what chunk granularity would actually serve the retriever well.
