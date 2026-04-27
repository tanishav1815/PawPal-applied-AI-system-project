# PawPal+ Loom Video Walkthrough Script

**Duration:** 4–5 minutes  
**Required elements:**
- ✅ End-to-end system run (2–3 inputs)
- ✅ AI feature behavior (RAG retrieval + Gemini response)
- ✅ Reliability/guardrails (logging, test results, or safety checks)
- ✅ Clear outputs for each case

---

## Pre-Recording Checklist

- [ ] Terminal is ready in the project directory
- [ ] `.env` file with `GEMINI_API_KEY` is set
- [ ] Streamlit app is **not** already running (we'll start it fresh on screen)
- [ ] Browser is ready for http://localhost:8501
- [ ] Another terminal is ready to show `pytest` results
- [ ] `pawpal.log` is ready to display (to show logging)
- [ ] Font size is zoomed in so text is readable on video
- [ ] Microphone is working and quiet

---

## Walkthrough Script (4–5 minutes)

### [00:00–00:15] **Introduction**
*Speak while showing the repo in VS Code*

> "Hi, I'm [Your Name]. This is PawPal+, an AI-powered pet care planner that combines rule-based scheduling with retrieval-augmented generation. The system asks for an owner's time budget and pets, builds a daily schedule respecting priority and time constraints, and uses a Gemini-powered AI advisor to answer questions about pet care grounded in a knowledge base. Let me walk you through the system end-to-end."

---

### [00:15–00:45] **Part 1: Start the app and set up an owner + pet**

*Action: Terminal → start the app*

```bash
streamlit run app.py
```

*Wait for "Local URL: http://localhost:8501"*

*Action: Click browser tab with the app*

**Narration:**
> "First, I'll set up an owner and a pet. The app has five sections: Owner setup, Pet management, Task entry, Schedule generation, and the AI Care Advisor. Let me start by creating an owner named Alex with 120 minutes available per day."

*Action: Fill out the owner form:*
- Name: `Alex`
- Available minutes: `120`
- Click "Save Owner"

*Action: Scroll down to Pet section*

**Narration:**
> "Now I'll add a pet. Let me add Mochi, a 3-year-old dog with no special needs."

*Action: Fill pet form:*
- Pet name: `Mochi`
- Species: `Dog`
- Age: `3`
- Special needs: (leave empty)
- Click "Add Pet"

*Wait a moment for UI to update*

---

### [00:45–01:30] **Part 2: Add tasks and generate schedule**

*Action: Scroll down to Task entry section*

**Narration:**
> "Now I'll add a few care tasks for Mochi. Let's add a morning walk, feeding, and playtime."

*Action: Add Task 1 (repeat 3 times):*

**Task 1:**
- Title: `Morning walk`
- Duration: `30` minutes
- Priority: `High`
- Category: `Exercise`
- Frequency: `Daily`
- Click "Add Task"

**Task 2:**
- Title: `Feeding`
- Duration: `10` minutes
- Priority: `High`
- Category: `Nutrition`
- Frequency: `Daily`
- Click "Add Task"

**Task 3:**
- Title: `Playtime`
- Duration: `20` minutes
- Priority: `Medium`
- Category: `Enrichment`
- Frequency: `Daily`
- Click "Add Task"

*Action: Scroll down to Schedule section*

**Narration:**
> "With 120 minutes available and tasks totaling 60 minutes, everything should fit. Let me generate the schedule."

*Action: Click "Generate Schedule"*

*Wait for the plan to display*

**Narration (while viewing schedule):**
> "The schedule is ordered by priority — high-priority tasks first, then medium. Within the same priority, shorter tasks come first to maximize the number of completed tasks. Mochi's morning walk (30 min, high), then feeding (10 min, high), then playtime (20 min, medium). Total: 60 minutes, well within the 120-minute budget. No conflicts detected."

---

### [01:30–03:00] **Part 3: AI Care Advisor — RAG + Gemini response**

*Action: Scroll down to AI Care Advisor section*

**Narration:**
> "Now for the AI feature — the PawPal Care Advisor. This uses Retrieval-Augmented Generation. When I ask a question about Mochi's care, the system first retrieves relevant paragraphs from a knowledge base using semantic embeddings, then sends that context plus Mochi's profile to Gemini for a grounded, contextual answer. Let me ask: 'Is Mochi getting enough exercise?'"

*Action: Type question:*
```
Is Mochi getting enough exercise?
```

*Action: Click "Ask AI Advisor"*

*Wait for response to load (10–15 seconds)*

*Action: Show the response on screen*

**Narration (while viewing response):**
> "Notice the response. The AI is drawing on specific knowledge base content — it mentions that adult dogs aged 1–7 years need 30–60 minutes of daily exercise, and it evaluates Mochi's 30-minute walk in that context. At the bottom, it shows the source files: 'dogs_exercise.md' and 'enrichment.md'. This is the RAG layer in action — the AI isn't just making up generic advice; it's retrieving concrete, fact-checked content first."

*Action: Scroll down to see the sources listed*

---

### [03:00–04:00] **Part 4: Reliability & Guardrails — Show test results**

*Action: Switch to terminal*

**Narration:**
> "To ensure reliability, I've built comprehensive tests covering both the scheduling logic and the RAG retriever. Let me run the full test suite."

*Action: Terminal → Run tests*

```bash
python -m pytest -v
```

*Wait for tests to complete*

*Action: Show the output* (highlight the summary line)

**Narration (while tests run or after):**
> "All 33 tests pass. That's 22 scheduling tests — covering priority ordering, time budgets, conflict detection, and recurrence — plus 11 RAG retriever tests that verify the system retrieves the correct knowledge base chunks for different pet species and care questions. None of these tests require an API key; they all run locally and are reproducible."

*Action: Show pawpal.log in terminal or editor*

```bash
tail -20 pawpal.log
```

**Narration:**
> "I also log every interaction. Here's the log showing the question I just asked, the retrieved chunks, and the Gemini response timestamp. This logging provides an audit trail for debugging and monitoring."

---

### [04:00–04:30] **Part 5: Quick second example (optional, shows flexibility)**

*Action: Go back to browser with Streamlit app*

**Narration (optional — only if time allows):**
> "Let me quickly ask a different question to show the system adapts based on query."

*Action: Type a different question:*
```
What medications might help Mochi with joint health?
```

*Action: Click "Ask AI Advisor"*

*Wait for response*

**Narration:**
> "This question triggers a different set of retrieved chunks — 'medications.md' and 'senior_pets.md' — because the system recognized the keywords 'medications' and 'joint health'. The retriever's semantic embeddings allow synonym-aware matching, so even paraphrased questions get relevant results."

---

### [04:30–04:45] **Closing**

**Narration:**
> "In summary, PawPal+ integrates deterministic scheduling with grounded AI. The scheduler ensures time-budgeted, conflict-free plans; the RAG advisor provides knowledge-base-backed answers; and the 33-test suite ensures both remain reliable and reproducible. The whole system is logged and transparent. Thanks for watching!"

---

## Key Talking Points (for reference while recording)

- **Architecture:** "Owner → Pet → Task chain, Scheduler for planning, RAGRetriever + Gemini for advisory."
- **RAG value:** "We retrieve knowledge first, then feed it to Gemini. This prevents hallucination and gives users source attribution."
- **Tests:** "33 tests, all pass, no API key needed — ensures the system is reproducible and trustworthy."
- **Logging:** "Every question and response is logged. This is critical for debugging and understanding what the AI actually saw."

---

## Recording Tips

1. **Speak clearly and slowly** — leave pauses so viewers can follow.
2. **Zoom in your terminal/editor** (font size ≥ 16) so text is readable.
3. **Click deliberately** so viewers see what you're doing.
4. **Let loading times show** — don't edit them out. It's honest to the user experience.
5. **Name specific features:** Say "semantic embeddings" and "retrieval-augmented generation" — don't just say "AI magic."

---

## Post-Recording

1. Upload to Loom
2. Copy the link
3. Paste into the README under "Demo Walkthrough" → replace `[Add Loom link here]` with the actual link
4. Commit and push to GitHub

Example:
```markdown
> 📹 Loom video link: https://www.loom.com/share/[your-id]
```

---

## Contingency

If Gemini API is unavailable during recording:
- You can show a recorded demo response (pre-screenshotted) and explain it
- Focus on the retriever tests and logging to demonstrate reliability
- Emphasize that the core scheduling logic is deterministic and fully testable without the API

Good luck with your recording! 🎥
