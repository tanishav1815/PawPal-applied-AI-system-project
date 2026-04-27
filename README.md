# PawPal+ — AI-Powered Pet Care Scheduler

> **Original project:** PawPal+ (Modules 1–3) was a Streamlit app for scheduling daily pet care tasks. It allowed owners to register pets, add care tasks with durations and priorities, and generate a time-budgeted daily plan ordered by priority. The scheduling, conflict detection, and recurring task logic were entirely rule-based with no AI component.
>
> This submission (Module 4) extends PawPal+ with a Retrieval-Augmented Generation (RAG) layer: a Claude-powered AI advisor that retrieves relevant pet care knowledge before answering questions about a specific pet's schedule and needs.

---

## Summary

PawPal+ is a smart pet care planning assistant that combines rule-based scheduling with AI-powered advice. Given a pet's profile and daily tasks, the system builds a priority-ordered, time-budgeted schedule and lets owners ask natural-language questions — "Is Mochi getting enough exercise?" or "How often should I groom Luna?" — answered by an AI that first retrieves relevant facts from a curated knowledge base before calling Claude.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app.py)                    │
│  Owner / Pet setup → Task entry → Schedule → AI Care Advisor    │
└────────────┬──────────────────────┬────────────────────────────┘
             │                      │
             ▼                      ▼
  ┌─────────────────┐    ┌──────────────────────────┐
  │ Scheduler        │    │ PawPalAdvisor             │
  │ (pawpal_system)  │    │ (ai_advisor.py)           │
  │                  │    │                           │
  │ build_plan()     │    │  1. RAGRetriever          │
  │ detect_conflicts │    │     └─ scores knowledge   │
  │ explain_plan()   │    │        base chunks by     │
  └─────────────────┘    │        keyword overlap     │
                          │                           │
                          │  2. Claude API call       │
                          │     (claude-sonnet-4-6)   │
                          │     with retrieved context│
                          │     + pet profile         │
                          │                           │
                          │  3. Logs to pawpal.log    │
                          └──────────────────────────┘
                                      │
                          ┌───────────▼──────────┐
                          │  knowledge_base/      │
                          │  dogs_exercise.md     │
                          │  cats_care.md         │
                          │  senior_pets.md       │
                          │  nutrition.md         │
                          │  grooming.md          │
                          │  medications.md       │
                          │  enrichment.md        │
                          └──────────────────────┘
```

**Data flow:**
1. Owner sets up their profile and pets in the Streamlit UI.
2. Tasks are added per pet; the Scheduler builds a priority-ordered daily plan.
3. In the AI Advisor section, the user types a question.
4. `RAGRetriever` scores all knowledge-base paragraphs against the query and returns the top 3 most relevant chunks.
5. `PawPalAdvisor` sends a Claude API call combining: the pet's profile, today's scheduled tasks, and the retrieved chunks.
6. Claude returns a grounded, contextual answer; the UI shows both the answer and the source files consulted.
7. Every interaction is logged to `pawpal.log`.

**UML class diagram:**

```mermaid
classDiagram
    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +bool completed
        +str frequency
        +date due_date
        +str start_time
        +is_doable(budget) bool
        +mark_complete() Task|None
        +describe() str
    }
    class Pet {
        +str name
        +str species
        +int age
        +list special_needs
        +add_task(task)
        +get_tasks() list
        +filter_tasks(completed) list
    }
    class Owner {
        +str name
        +int available_minutes
        +add_pet(pet)
        +get_pets() list
        +get_all_tasks() list
    }
    class Scheduler {
        +build_plan() list
        +detect_conflicts() list
        +explain_plan() str
        +sort_by_duration() list
    }
    class RAGRetriever {
        +retrieve(query, top_k) list
        +chunk_count int
    }
    class PawPalAdvisor {
        +advise(question, pet, tasks) dict
    }
    Owner --> Pet : owns
    Pet --> Task : has
    Scheduler --> Owner : reads budget
    Scheduler --> Pet : schedules tasks
    PawPalAdvisor --> RAGRetriever : retrieves context
    PawPalAdvisor --> Pet : reads profile
```

---

## Setup Instructions

### Prerequisites

- Python 3.9 or higher (tested on 3.12)
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### Install

```bash
git clone <repo-url>
cd PawPal-applied-AI-system-project
pip install -r requirements.txt
```

### Configure API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # macOS / Linux
# or
set ANTHROPIC_API_KEY=sk-ant-...      # Windows Command Prompt
```

### Run the app

```bash
streamlit run app.py
```

### Run tests

```bash
python -m pytest
```

Expected output: **33 passed** (22 scheduling tests + 11 RAG retriever tests).

---

## Sample Interactions

### Example 1 — Exercise check for a young dog

**Pet:** Mochi, dog, 3 years old  
**Scheduled tasks:** Morning walk (30 min, high), Trick training (20 min, low)  
**Question:** "Is Mochi getting enough exercise?"

**PawPal AI response:**
> Based on the guidelines for adult dogs, Mochi is doing well but could benefit from a bit more activity. Adult dogs (1–7 years) generally need at least 30–60 minutes of daily exercise. Mochi's morning walk covers 30 minutes, which meets the minimum, but adding the trick training brings total activity to 50 minutes — right in the ideal range for a medium-energy adult dog. If Mochi is a larger or high-energy breed, consider extending one walk or adding an evening session.

**Sources consulted:** `dogs_exercise.md`, `enrichment.md`

---

### Example 2 — Grooming frequency for a cat

**Pet:** Luna, cat, 5 years old  
**Scheduled tasks:** Brush coat (10 min, medium)  
**Question:** "How often should I brush Luna?"

**PawPal AI response:**
> For a short-haired adult cat like Luna, brushing once or twice per week is typically sufficient to reduce shedding and prevent hairballs. The once-weekly brush in Luna's schedule meets the minimum recommendation. If Luna has a longer or denser coat, daily brushing would be more appropriate. Since you haven't noted a specific breed, once or twice weekly is a great baseline to keep her coat healthy.

**Sources consulted:** `grooming.md`, `cats_care.md`

---

### Example 3 — Care advice for a senior pet

**Pet:** Max, dog, 9 years old, special needs: arthritis  
**Scheduled tasks:** Morning walk (30 min, high)  
**Question:** "What should I keep in mind for Max given his age and arthritis?"

**PawPal AI response:**
> At 9 years, Max is solidly in senior territory for most breeds. A few things to consider: his 30-minute morning walk is fine but watch for signs of fatigue — limping during the walk, stiffness afterward, or reluctance to start. If you see those signs, splitting it into two shorter walks of 15 minutes each is gentler on arthritic joints. Low-impact exercise (leisurely walking, gentle swimming) is ideal. Also, twice-yearly vet check-ups are recommended for senior dogs to monitor joint health and catch any age-related conditions early. Orthopedic bedding can also help with comfort.

**Sources consulted:** `senior_pets.md`, `dogs_exercise.md`

---

## Design Decisions

**Why RAG over a plain LLM call?**  
A plain Claude call with just the pet's profile would produce plausible-sounding but generic advice — it would have no way to distinguish between what the knowledge base specifically says and what it's extrapolating. RAG forces the system to retrieve concrete, fact-checked content before generating a response. The UI displays the source files consulted, so users can verify the AI is drawing on real content rather than hallucinating.

**Why keyword overlap instead of vector embeddings?**  
Keyword overlap (word intersection scored by query length) requires zero additional dependencies and no embedding API calls. For a curated 7-file knowledge base with consistent vocabulary, it performs as well as semantic search for the majority of queries. The trade-off is that synonym-heavy queries may retrieve weaker context — this is explicitly documented as a known limitation in `model_card.md` and is the natural upgrade path (swap in ChromaDB + an embedding model).

**Why paragraph-level chunking?**  
Each paragraph in the knowledge files is a complete thought (e.g., "Adult dogs need X minutes of exercise"). Splitting at the sentence level would fragment context; splitting at the document level would make retrieval coarse. Paragraphs give the AI enough context to reason while keeping retrieved chunks specific.

**Why keep the scheduler and the AI advisor separate?**  
The scheduler is deterministic and testable — given the same inputs, it always produces the same plan. The AI advisor is probabilistic. Mixing them would make the scheduling logic untestable. The separation means 22 scheduler tests can run without any API key, while the AI tests (11 tests) are also API-key-free because they only test the retriever.

---

## Testing Summary

| Test file | Tests | Coverage area |
|---|---|---|
| `tests/test_pawpal.py` | 22 | Task, Pet, Owner, Scheduler logic |
| `tests/test_ai_advisor.py` | 11 | RAGRetriever loading, relevance, edge cases |
| **Total** | **33** | **All 33 pass** |

**Key results:**
- All species-specific queries retrieved the correct source files (dogs_exercise, cats_care, senior_pets, etc.).
- `test_dog_query_differs_from_cat_query` passes, proving that RAG retrieval produces different context for different species — the core requirement for meaningful RAG integration.
- Empty query and missing-directory edge cases are handled without exceptions.
- Scheduler tests confirm that priority ordering, time budget enforcement, and conflict detection all remain correct after the AI integration.

**What worked:** The paragraph-level chunking combined with query-length normalization produced reliable species and category differentiation without any embedding model.

**What didn't work:** Very short or vague queries (one or two words) retrieve low-quality chunks because there is insufficient vocabulary to differentiate between files. This is expected behavior for keyword overlap and is logged.

---

## Reflection

Building PawPal+ taught me that the hardest part of an AI system is not the model call — it's the data pipeline upstream of the model. Getting the retriever to return the *right* content for a given question required careful decisions about chunking, scoring, and vocabulary alignment between the knowledge base and likely user queries. A model call on bad context produces a confident-sounding wrong answer, which is worse than no answer.

The project also showed that separation of concerns matters as much in AI systems as in traditional software. Keeping the deterministic scheduler separate from the probabilistic AI advisor meant I could write 33 fully reproducible tests, none of which require an API key or internet access. That reliability is what makes the system trustworthy in practice.

---

## Demo Walkthrough

> 📹 Loom video link: _[to be added before submission]_

---

## Repository Structure

```
PawPal-applied-AI-system-project/
├── app.py                  # Streamlit UI (5 sections including AI Advisor)
├── pawpal_system.py        # Core scheduling logic (Task, Pet, Owner, Scheduler)
├── ai_advisor.py           # RAGRetriever + PawPalAdvisor
├── main.py                 # CLI demo of backend logic
├── requirements.txt
├── model_card.md           # Reflection, limitations, AI collaboration notes
├── knowledge_base/
│   ├── dogs_exercise.md
│   ├── cats_care.md
│   ├── senior_pets.md
│   ├── nutrition.md
│   ├── grooming.md
│   ├── medications.md
│   └── enrichment.md
├── tests/
│   ├── test_pawpal.py      # 22 scheduling tests
│   └── test_ai_advisor.py  # 11 RAG retriever tests
└── assets/                 # Screenshots and diagrams
```
