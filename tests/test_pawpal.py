"""
Tests for PawPal+ core logic.
Run with: python -m pytest
"""

from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_is_doable_true_when_fits():
    """is_doable returns True when duration <= budget."""
    task = Task(title="Quick feed", duration_minutes=10, priority="medium")
    assert task.is_doable(10) is True
    assert task.is_doable(20) is True


def test_is_doable_false_when_too_long():
    """is_doable returns False when duration exceeds budget."""
    task = Task(title="Long groom", duration_minutes=45, priority="low")
    assert task.is_doable(30) is False


def test_mark_complete_daily_recurrence():
    """mark_complete() on a daily task should return a new task due tomorrow."""
    today = date.today()
    task = Task(title="Feed", duration_minutes=10, priority="high",
                frequency="daily", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_mark_complete_weekly_recurrence():
    """mark_complete() on a weekly task should return a new task due in 7 days."""
    today = date.today()
    task = Task(title="Bath", duration_minutes=20, priority="medium",
                frequency="weekly", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_mark_complete_one_time_returns_none():
    """mark_complete() on a non-recurring task should return None."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high")
    result = task.mark_complete()
    assert result is None


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    assert len(pet.get_tasks()) == 1


def test_add_multiple_tasks():
    """Pet should hold all added tasks."""
    pet = Pet(name="Luna", species="cat", age=2)
    pet.add_task(Task("Feed",  duration_minutes=10, priority="high"))
    pet.add_task(Task("Brush", duration_minutes=5,  priority="low"))
    assert len(pet.get_tasks()) == 2


def test_filter_tasks_pending():
    """filter_tasks(completed=False) should return only pending tasks."""
    pet = Pet(name="Mochi", species="dog", age=3)
    t1 = Task("Walk",  duration_minutes=20, priority="high")
    t2 = Task("Train", duration_minutes=10, priority="low")
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    pending = pet.filter_tasks(completed=False)
    assert len(pending) == 1
    assert pending[0].title == "Train"


def test_filter_tasks_completed():
    """filter_tasks(completed=True) should return only completed tasks."""
    pet = Pet(name="Mochi", species="dog", age=3)
    t1 = Task("Walk",  duration_minutes=20, priority="high")
    t2 = Task("Train", duration_minutes=10, priority="low")
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    done = pet.filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0].title == "Walk"


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_scheduler_respects_time_budget():
    """build_plan should not exceed the available time budget."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk",  duration_minutes=20, priority="high"))
    pet.add_task(Task("Train", duration_minutes=20, priority="medium"))  # won't fit

    owner.add_pet(pet)
    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert sum(t.duration_minutes for t in plan) <= 30


def test_scheduler_orders_by_priority():
    """High priority tasks should appear before lower priority ones in the plan."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Trick training", duration_minutes=20, priority="low"))
    pet.add_task(Task("Morning walk",   duration_minutes=30, priority="high"))
    pet.add_task(Task("Grooming",       duration_minutes=10, priority="medium"))

    owner.add_pet(pet)
    plan = Scheduler(owner=owner, pet=pet).build_plan()
    priorities = [t.priority for t in plan]
    assert priorities == sorted(priorities, key=lambda p: {"high": 0, "medium": 1, "low": 2}[p])


def test_scheduler_empty_plan_when_no_time():
    """build_plan should return an empty list when budget is 0."""
    owner = Owner(name="Jordan", available_minutes=0)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))

    owner.add_pet(pet)
    assert Scheduler(owner=owner, pet=pet).build_plan() == []


def test_scheduler_skips_completed_tasks():
    """build_plan should exclude already-completed tasks."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Mochi", species="dog", age=3)
    t = Task("Walk", duration_minutes=20, priority="high")
    t.mark_complete()
    pet.add_task(t)

    owner.add_pet(pet)
    assert Scheduler(owner=owner, pet=pet).build_plan() == []


def test_sort_by_duration():
    """sort_by_duration should return tasks ordered shortest to longest."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Long task",   duration_minutes=40, priority="high"))
    pet.add_task(Task("Short task",  duration_minutes=5,  priority="low"))
    pet.add_task(Task("Medium task", duration_minutes=20, priority="medium"))

    owner.add_pet(pet)
    sorted_tasks = Scheduler(owner=owner, pet=pet).sort_by_duration()
    durations = [t.duration_minutes for t in sorted_tasks]
    assert durations == sorted(durations)


def test_detect_conflicts_found():
    """detect_conflicts should catch two tasks whose time ranges overlap."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Luna", species="cat", age=2)
    pet.add_task(Task("Feed",  duration_minutes=15, priority="high", start_time="07:00"))
    pet.add_task(Task("Brush", duration_minutes=10, priority="high", start_time="07:10"))  # overlaps

    owner.add_pet(pet)
    conflicts = Scheduler(owner=owner, pet=pet).detect_conflicts()
    assert len(conflicts) == 1
    assert "Feed" in conflicts[0]
    assert "Brush" in conflicts[0]


def test_detect_conflicts_none():
    """detect_conflicts should return empty list when tasks don't overlap."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Luna", species="cat", age=2)
    pet.add_task(Task("Feed",  duration_minutes=10, priority="high", start_time="07:00"))
    pet.add_task(Task("Brush", duration_minutes=10, priority="high", start_time="07:30"))  # no overlap

    owner.add_pet(pet)
    assert Scheduler(owner=owner, pet=pet).detect_conflicts() == []
