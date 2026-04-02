import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — initialise once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set when the owner form is submitted


# ---------------------------------------------------------------------------
# Step 1: Owner setup
# ---------------------------------------------------------------------------
st.header("Owner")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Free time today (minutes)", min_value=10, max_value=480, value=90
    )
    submitted = st.form_submit_button("Save owner")
    if submitted:
        st.session_state.owner = Owner(
            name=owner_name, available_minutes=int(available_minutes)
        )
        st.success(f"Owner '{owner_name}' saved with {available_minutes} min available.")

if st.session_state.owner is None:
    st.info("Fill in your name and free time above to get started.")
    st.stop()

owner: Owner = st.session_state.owner


# ---------------------------------------------------------------------------
# Step 2: Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("Pets")

with st.form("pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    special_needs = st.text_input("Special needs (comma-separated, optional)", value="")
    add_pet = st.form_submit_button("Add pet")
    if add_pet:
        needs = [n.strip() for n in special_needs.split(",") if n.strip()]
        new_pet = Pet(name=pet_name, species=species, age=int(age), special_needs=needs)
        owner.add_pet(new_pet)
        st.success(f"Pet '{pet_name}' added to {owner.name}'s profile.")

pets = owner.get_pets()
if pets:
    st.write(f"**{owner.name}'s pets:** {', '.join(p.name for p in pets)}")
else:
    st.info("No pets yet — add one above.")
    st.stop()


# ---------------------------------------------------------------------------
# Step 3: Add tasks to a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("Tasks")

selected_pet_name = st.selectbox("Add a task to:", [p.name for p in pets])
selected_pet = next(p for p in pets if p.name == selected_pet_name)

with st.form("task_form"):
    task_title = st.text_input("Task title", value="Morning walk")
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    priority = st.selectbox("Priority", ["high", "medium", "low"])
    category = st.selectbox("Category", ["exercise", "feeding", "grooming", "medication", "enrichment", "other"])
    add_task = st.form_submit_button("Add task")
    if add_task:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
        )
        selected_pet.add_task(task)
        st.success(f"Task '{task_title}' added to {selected_pet.name}.")

# Show all current tasks per pet
for pet in pets:
    tasks = pet.get_tasks()
    if tasks:
        st.write(f"**{pet.name}'s tasks:**")
        st.table(
            [
                {
                    "Title": t.title,
                    "Category": t.category,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Done": "✅" if t.completed else "—",
                }
                for t in tasks
            ]
        )


# ---------------------------------------------------------------------------
# Step 4: Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("Generate Schedule")

schedule_pet_name = st.selectbox("Schedule for:", [p.name for p in pets], key="sched_pet")
schedule_pet = next(p for p in pets if p.name == schedule_pet_name)

if st.button("Build schedule"):
    if not schedule_pet.get_tasks():
        st.warning(f"{schedule_pet.name} has no tasks yet.")
    else:
        scheduler = Scheduler(owner=owner, pet=schedule_pet)
        plan = scheduler.build_plan()

        st.subheader(f"Today's plan for {schedule_pet.name}")
        st.text(scheduler.explain_plan())

        st.write("**Scheduled tasks:**")
        st.table(
            [
                {
                    "Title": t.title,
                    "Priority": t.priority,
                    "Duration (min)": t.duration_minutes,
                }
                for t in plan
            ]
        )

        skipped = [t for t in schedule_pet.get_tasks() if t not in plan]
        if skipped:
            st.warning(
                f"Skipped (didn't fit in {owner.available_minutes} min): "
                + ", ".join(t.title for t in skipped)
            )
