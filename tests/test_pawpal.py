"""
Tests for PawPal+ core logic.
Run with: python -m pytest
"""

import pytest
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
    scheduler = Scheduler(owner=owner, pet=pet)
    plan = scheduler.build_plan()

    total = sum(t.duration_minutes for t in plan)
    assert total <= 30


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
    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert plan == []
