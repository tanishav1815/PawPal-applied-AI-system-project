# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML includes four classes:

- Task (dataclass): holds a single care action — title, duration, priority, and category. Responsible for knowing whether it fits in a time budget (`is_doable`) and describing itself.
- Pet (dataclass): holds pet identity (name, species, age, special needs) and owns a list of Tasks. Responsible for managing and exposing its task list.
- Owner (dataclass): holds owner identity, total available minutes per day, and preferences. Responsible for managing a list of Pets.
- Scheduler: takes an Owner and a Pet, then builds an ordered daily plan (`build_plan`) and explains it in plain English (`explain_plan`). It is the only class with scheduling logic.

Relationships: Owner → Pet (one-to-many), Pet → Task (one-to-many), Scheduler uses Owner + Pet to produce a plan.

**b. Design changes**

Two changes were made during implementation:

1. **Added `completed` field and `mark_complete()` to `Task`** — the skeleton had no way to track whether a task was done. This was needed for tests and for future UI display (showing checked-off tasks).

2. **Added `get_all_tasks()` to `Owner`** — the skeleton only had `get_pets()`. The Scheduler needed a way to pull every (pet, task) pair from the owner without reaching into each Pet's internals directly. Adding this method keeps the logic clean and avoids tight coupling between Scheduler and Pet.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: available time (tasks are dropped if they exceed the remaining budget), task priority (high → medium → low), and completion state (completed tasks are excluded from the plan). Priority was ranked first because a missed high-priority task (e.g. medication) has real consequences, whereas a missed enrichment task does not.

**b. Tradeoffs**

Conflict detection only flags exact `start_time` overlaps — it does not account for tasks that have no `start_time` set. This means two untimed tasks could end up scheduled back-to-back without a conflict warning even if a real owner couldn't do both at once. The tradeoff is simplicity: requiring a start_time for every task would make the app harder to use for quick task entry, while the lightweight check still catches the most common scheduling mistake (accidentally double-booking a specific time slot).

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
