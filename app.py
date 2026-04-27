import os

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

try:
    from ai_advisor import PawPalAdvisor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your smart pet care planning assistant.")

# ---------------------------------------------------------------------------
# Session state — initialise once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None


# ---------------------------------------------------------------------------
# Section 1: Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Free time today (minutes)", min_value=10, max_value=480, value=90
    )
    if st.form_submit_button("Save owner"):
        st.session_state.owner = Owner(
            name=owner_name, available_minutes=int(available_minutes)
        )
        st.success(f"Saved — {owner_name} has {available_minutes} min today.")

if st.session_state.owner is None:
    st.info("Fill in your details above to get started.")
    st.stop()

owner: Owner = st.session_state.owner


# ---------------------------------------------------------------------------
# Section 2: Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Pets")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    pet_name      = col1.text_input("Name", value="Mochi")
    species       = col2.selectbox("Species", ["dog", "cat", "other"])
    age           = col3.number_input("Age (yrs)", min_value=0, max_value=30, value=3)
    special_needs = st.text_input("Special needs (comma-separated, optional)", value="")
    if st.form_submit_button("Add pet"):
        needs = [n.strip() for n in special_needs.split(",") if n.strip()]
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age), special_needs=needs))
        st.success(f"{pet_name} added.")

pets = owner.get_pets()
if not pets:
    st.info("No pets yet — add one above.")
    st.stop()

st.write(f"**{owner.name}'s pets:** {', '.join(p.name for p in pets)}")


# ---------------------------------------------------------------------------
# Section 3: Add tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Tasks")

selected_pet_name = st.selectbox("Add a task to:", [p.name for p in pets])
selected_pet = next(p for p in pets if p.name == selected_pet_name)

with st.form("task_form"):
    col1, col2 = st.columns(2)
    task_title = col1.text_input("Task title", value="Morning walk")
    start_time = col2.text_input("Start time (HH:MM, optional)", value="")

    col3, col4, col5 = st.columns(3)
    duration  = col3.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority  = col4.selectbox("Priority", ["high", "medium", "low"])
    category  = col5.selectbox("Category", ["exercise", "feeding", "grooming", "medication", "enrichment", "other"])

    col6, col7 = st.columns(2)
    frequency = col6.selectbox("Frequency", ["", "daily", "weekly"], format_func=lambda x: x or "one-time")

    if st.form_submit_button("Add task"):
        selected_pet.add_task(Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            start_time=start_time.strip(),
            frequency=frequency,
        ))
        st.success(f"'{task_title}' added to {selected_pet.name}.")

# Show task tables per pet, with sort toggle
for pet in pets:
    tasks = pet.get_tasks()
    if not tasks:
        continue

    sched = Scheduler(owner=owner, pet=pet)
    view = st.radio(
        f"View {pet.name}'s tasks as:",
        ["Added order", "Sorted by duration (shortest first)", "Pending only", "Completed only"],
        horizontal=True,
        key=f"view_{pet.name}",
    )

    if view == "Sorted by duration (shortest first)":
        display = sched.sort_by_duration()
    elif view == "Pending only":
        display = pet.filter_tasks(completed=False)
    elif view == "Completed only":
        display = pet.filter_tasks(completed=True)
    else:
        display = tasks

    if display:
        st.write(f"**{pet.name}'s tasks** ({len(display)} shown):")
        st.table([
            {
                "Title":         t.title,
                "Category":      t.category,
                "Duration (min)": t.duration_minutes,
                "Priority":      t.priority,
                "Frequency":     t.frequency or "one-time",
                "Start time":    t.start_time or "—",
                "Done":          "✅" if t.completed else "—",
            }
            for t in display
        ])
    else:
        st.info(f"No tasks match the selected filter for {pet.name}.")


# ---------------------------------------------------------------------------
# Section 4: Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Generate Schedule")

schedule_pet_name = st.selectbox("Build a plan for:", [p.name for p in pets], key="sched_pet")
schedule_pet = next(p for p in pets if p.name == schedule_pet_name)

if st.button("Build schedule", type="primary"):
    if not schedule_pet.get_tasks():
        st.warning(f"{schedule_pet.name} has no tasks yet — add some above.")
    else:
        sched = Scheduler(owner=owner, pet=schedule_pet)
        plan  = sched.build_plan()

        if not plan:
            st.error(f"No tasks fit within {owner.available_minutes} minutes.")
        else:
            st.success(f"Plan ready — {len(plan)} task(s) scheduled.")

            # Time-slot explanation
            with st.expander("View full plan explanation", expanded=True):
                st.code(sched.explain_plan(), language=None)

            # Scheduled tasks table
            st.subheader("Scheduled tasks")
            elapsed = 0
            rows = []
            for t in plan:
                rows.append({
                    "Title":         t.title,
                    "Priority":      t.priority,
                    "Duration (min)": t.duration_minutes,
                    "Slot":          f"{elapsed}–{elapsed + t.duration_minutes} min",
                    "Category":      t.category,
                })
                elapsed += t.duration_minutes
            st.table(rows)

            # Skipped tasks
            skipped = [t for t in schedule_pet.get_tasks() if t not in plan and not t.completed]
            if skipped:
                st.warning(
                    f"⏭  Skipped (didn't fit in {owner.available_minutes} min): "
                    + ", ".join(f"**{t.title}**" for t in skipped)
                )

            # Conflict warnings
            conflicts = sched.detect_conflicts()
            if conflicts:
                st.subheader("⚠️  Scheduling conflicts detected")
                for w in conflicts:
                    st.warning(w)
                st.caption(
                    "Tip: adjust start times so tasks don't overlap, "
                    "or leave the start time blank to let the scheduler assign slots automatically."
                )
            else:
                st.success("No time conflicts detected.")

            # Progress metrics
            st.divider()
            total_pending    = len(schedule_pet.filter_tasks(completed=False))
            total_completed  = len(schedule_pet.filter_tasks(completed=True))
            time_used        = sum(t.duration_minutes for t in plan)

            c1, c2, c3 = st.columns(3)
            c1.metric("Tasks scheduled", len(plan))
            c2.metric("Time used", f"{time_used} min", delta=f"{owner.available_minutes - time_used} min free")
            c3.metric("Completed today", total_completed)


# ---------------------------------------------------------------------------
# Section 5: AI Care Advisor (RAG + Claude)
# ---------------------------------------------------------------------------
st.divider()
st.header("5. AI Care Advisor")
st.caption("Ask a question about your pet's care — PawPal AI retrieves relevant knowledge before answering.")

if not AI_AVAILABLE:
    st.error("ai_advisor.py could not be imported. Make sure `google-genai` is installed (`pip install google-genai`).")
elif not os.getenv("GEMINI_API_KEY"):
    st.warning(
        "Set `GEMINI_API_KEY` in your `.env` file to enable the AI advisor.  \n"
        "Get a free key at https://aistudio.google.com"
    )
else:
    advisor_pet_name = st.selectbox("Ask about:", [p.name for p in pets], key="advisor_pet")
    advisor_pet = next(p for p in pets if p.name == advisor_pet_name)

    question = st.text_input(
        "Your question",
        placeholder="e.g. Is Mochi getting enough exercise? How often should I groom Luna?",
        key="ai_question",
    )

    if st.button("Ask AI", type="primary"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Searching knowledge base and consulting Gemini..."):
                if "advisor" not in st.session_state:
                    st.session_state.advisor = PawPalAdvisor()
                advisor = st.session_state.advisor
                sched = Scheduler(owner=owner, pet=advisor_pet)
                plan = sched.build_plan()
                result = advisor.advise(
                    question=question,
                    pet=advisor_pet,
                    scheduled_tasks=plan,
                )

            if result["error"]:
                st.error(f"AI error: {result['error']}")
            else:
                st.markdown("**PawPal AI:**")
                st.markdown(result["response"])
                if result["sources"]:
                    st.caption(
                        "Knowledge sources consulted: "
                        + ", ".join(f"`{s}`" for s in result["sources"])
                    )
