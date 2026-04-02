"""
main.py — demo script for PawPal+ backend logic.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    jordan = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5)

    # Tasks added intentionally OUT OF ORDER (duration) to demo sorting
    mochi.add_task(Task("Evening walk",   duration_minutes=40, priority="medium", category="exercise",    start_time="17:00"))
    mochi.add_task(Task("Breakfast feed", duration_minutes=10, priority="high",   category="feeding",     start_time="07:00"))
    mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="exercise",    start_time="07:30"))
    mochi.add_task(Task("Teeth brushing", duration_minutes=5,  priority="medium", category="grooming",    start_time="08:00"))
    mochi.add_task(Task("Trick training", duration_minutes=20, priority="low",    category="enrichment",  start_time="10:00",
                        frequency="daily", due_date=date.today()))

    luna.add_task(Task("Breakfast feed", duration_minutes=10, priority="high",   category="feeding",     start_time="07:05"))
    luna.add_task(Task("Brush coat",     duration_minutes=10, priority="medium", category="grooming"))
    luna.add_task(Task("Laser toy play", duration_minutes=15, priority="low",    category="enrichment"))

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ------------------------------------------------------------------
    # 1. Schedule and explain plans
    # ------------------------------------------------------------------
    for pet in jordan.get_pets():
        sched = Scheduler(owner=jordan, pet=pet)
        print("=" * 60)
        print(sched.explain_plan())
        print()

    # ------------------------------------------------------------------
    # 2. Sort Mochi's tasks by duration (shortest first)
    # ------------------------------------------------------------------
    sched_mochi = Scheduler(owner=jordan, pet=mochi)
    print("=" * 60)
    print("Mochi's tasks sorted by duration:")
    for t in sched_mochi.sort_by_duration():
        print(f"  {t.duration_minutes:>3} min  {t.title}")

    # ------------------------------------------------------------------
    # 3. Filter — pending vs completed tasks
    # ------------------------------------------------------------------
    print()
    print("Mochi's pending tasks:")
    for t in mochi.filter_tasks(completed=False):
        print(f"  {t.describe()}")

    # Mark one task complete and get its recurrence
    trick = next(t for t in mochi.get_tasks() if t.title == "Trick training")
    next_occurrence = trick.mark_complete()
    print(f"\nMarked '{trick.title}' complete.")
    if next_occurrence:
        mochi.add_task(next_occurrence)
        print(f"Recurring task auto-created: '{next_occurrence.title}' due {next_occurrence.due_date}")

    print("\nMochi's completed tasks:")
    for t in mochi.filter_tasks(completed=True):
        print(f"  {t.describe()}")

    # ------------------------------------------------------------------
    # 4. Filter by pet name via Owner
    # ------------------------------------------------------------------
    print()
    print("All Luna tasks (via owner.filter_tasks_by_pet):")
    for t in jordan.filter_tasks_by_pet("Luna"):
        print(f"  {t.describe()}")

    # ------------------------------------------------------------------
    # 5. Conflict detection — add two overlapping tasks to Luna
    # ------------------------------------------------------------------
    luna.add_task(Task("Dinner feed",   duration_minutes=10, priority="high", category="feeding",  start_time="07:05"))
    luna.add_task(Task("Evening brush", duration_minutes=10, priority="low",  category="grooming", start_time="07:10"))

    sched_luna = Scheduler(owner=jordan, pet=luna)
    conflicts = sched_luna.detect_conflicts()
    print()
    print("Conflict check for Luna:")
    if conflicts:
        for w in conflicts:
            print(f"  ⚠  {w}")
    else:
        print("  No conflicts detected.")

    # ------------------------------------------------------------------
    # 6. All tasks across all pets
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("All registered tasks:")
    for pet, task in jordan.get_all_tasks():
        print(f"  [{pet.name}] {task.describe()}")


if __name__ == "__main__":
    main()
