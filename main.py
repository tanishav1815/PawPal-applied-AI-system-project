"""
main.py — demo script to verify PawPal+ backend logic in the terminal.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Create owner ---
    jordan = Owner(name="Jordan", available_minutes=90)

    # --- Create pets ---
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    # --- Add tasks to Mochi ---
    mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="exercise"))
    mochi.add_task(Task("Breakfast feed", duration_minutes=10, priority="high",   category="feeding"))
    mochi.add_task(Task("Teeth brushing", duration_minutes=5,  priority="medium", category="grooming"))
    mochi.add_task(Task("Trick training", duration_minutes=20, priority="low",    category="enrichment"))
    mochi.add_task(Task("Evening walk",   duration_minutes=40, priority="medium", category="exercise"))

    # --- Add tasks to Luna ---
    luna.add_task(Task("Breakfast feed",  duration_minutes=10, priority="high",   category="feeding"))
    luna.add_task(Task("Brush coat",      duration_minutes=10, priority="medium", category="grooming"))
    luna.add_task(Task("Laser toy play",  duration_minutes=15, priority="low",    category="enrichment"))

    # --- Register pets with owner ---
    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # --- Schedule for each pet and print ---
    for pet in jordan.get_pets():
        scheduler = Scheduler(owner=jordan, pet=pet)
        print("=" * 55)
        print(scheduler.explain_plan())
        print()

    # --- Show all tasks across all pets ---
    print("=" * 55)
    print("All registered tasks:")
    for pet, task in jordan.get_all_tasks():
        print(f"  [{pet.name}] {task.describe()}")


if __name__ == "__main__":
    main()
