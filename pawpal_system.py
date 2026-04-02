"""
PawPal+ — core backend logic.
Classes: Task, Pet, Owner, Scheduler.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """Represents a single pet care activity with time, priority, recurrence, and completion state."""

    title: str
    duration_minutes: int
    priority: str               # "low" | "medium" | "high"
    category: str = ""          # e.g. "feeding", "exercise", "grooming", "medication"
    completed: bool = False
    frequency: str = ""         # "" = one-time | "daily" | "weekly"
    due_date: Optional[date] = None
    start_time: str = ""        # "HH:MM" — optional scheduled start time

    def is_doable(self, budget: int) -> bool:
        """Return True if this task fits within the remaining time budget (minutes)."""
        return self.duration_minutes <= budget

    def mark_complete(self) -> Optional[Task]:
        """
        Mark this task as completed.
        If the task recurs, return a new Task instance due on the next occurrence;
        otherwise return None.
        """
        self.completed = True
        if self.frequency == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                frequency=self.frequency,
                due_date=next_due,
                start_time=self.start_time,
            )
        if self.frequency == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                frequency=self.frequency,
                due_date=next_due,
                start_time=self.start_time,
            )
        return None

    def describe(self) -> str:
        """Return a human-readable one-line description of the task."""
        status = "done" if self.completed else "pending"
        cat = f" [{self.category}]" if self.category else ""
        recur = f" | {self.frequency}" if self.frequency else ""
        due = f" | due {self.due_date}" if self.due_date else ""
        time = f" | @{self.start_time}" if self.start_time else ""
        return f"{self.title}{cat} — {self.duration_minutes} min | {self.priority}{recur}{due}{time} | {status}"


@dataclass
class Pet:
    """Stores a pet's identity and its list of care tasks."""

    name: str
    species: str            # e.g. "dog", "cat", "other"
    age: int                # in years
    special_needs: list[str] = field(default_factory=list)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks registered for this pet."""
        return list(self._tasks)

    def filter_tasks(self, completed: Optional[bool] = None) -> list[Task]:
        """
        Return tasks filtered by completion status.
        Pass completed=True for done tasks, False for pending, None for all.
        """
        if completed is None:
            return self.get_tasks()
        return [t for t in self._tasks if t.completed == completed]


@dataclass
class Owner:
    """Manages owner identity, time availability, and their collection of pets."""

    name: str
    available_minutes: int          # total free minutes per day
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Register a Pet under this owner."""
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self._pets)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self._pets for task in pet.get_tasks()]

    def filter_tasks_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to the pet with the given name."""
        for pet in self._pets:
            if pet.name == pet_name:
                return pet.get_tasks()
        return []


@dataclass
class Scheduler:
    """Retrieves tasks from an Owner's pets and builds a prioritized daily plan."""

    owner: Owner
    pet: Pet
    time_budget: Optional[int] = None   # defaults to owner.available_minutes if None

    def _effective_budget(self) -> int:
        """Return the active time budget in minutes."""
        return self.time_budget if self.time_budget is not None else self.owner.available_minutes

    def sort_by_duration(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted by duration (shortest first). Uses pet's tasks if none given."""
        source = tasks if tasks is not None else self.pet.get_tasks()
        return sorted(source, key=lambda t: t.duration_minutes)

    def build_plan(self) -> list[Task]:
        """
        Select pending tasks for the pet that fit within the time budget.
        Ordered high → medium → low priority; shorter tasks preferred within the same priority.
        """
        candidates = sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )
        budget = self._effective_budget()
        plan: list[Task] = []
        for task in candidates:
            if task.is_doable(budget):
                plan.append(task)
                budget -= task.duration_minutes
        return plan

    def detect_conflicts(self) -> list[str]:
        """
        Check scheduled tasks for overlapping time slots.
        Only tasks with a start_time ("HH:MM") are considered.
        Returns a list of warning strings; empty list means no conflicts.
        """
        timed = [t for t in self.build_plan() if t.start_time]
        timed.sort(key=lambda t: t.start_time)

        warnings: list[str] = []
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i + 1]
            a_end_h, a_end_m = _add_minutes(a.start_time, a.duration_minutes)
            b_h, b_m = map(int, b.start_time.split(":"))
            if (a_end_h, a_end_m) > (b_h, b_m):
                warnings.append(
                    f"CONFLICT: '{a.title}' (ends {a_end_h:02d}:{a_end_m:02d}) "
                    f"overlaps with '{b.title}' (starts {b.start_time})"
                )
        return warnings

    def explain_plan(self) -> str:
        """
        Return a plain-English explanation of the generated plan,
        showing each task's slot and why it was chosen, plus any conflicts.
        """
        plan = self.build_plan()
        if not plan:
            return f"No tasks fit within {self._effective_budget()} minutes for {self.pet.name}."

        lines = [
            f"Daily plan for {self.pet.name} ({self.owner.name} has {self._effective_budget()} min available):",
            "",
        ]
        elapsed = 0
        for i, task in enumerate(plan, 1):
            start, end = elapsed, elapsed + task.duration_minutes
            reason = "high priority" if task.priority == "high" else f"{task.priority} priority"
            lines.append(f"  {i}. [{start:>3}–{end:<3} min] {task.title}  ({reason})")
            elapsed = end

        lines.append(f"\nTotal time used: {elapsed} min / {self._effective_budget()} min available.")

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("\nWarnings:")
            for w in conflicts:
                lines.append(f"  ⚠  {w}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _add_minutes(hhmm: str, minutes: int) -> tuple[int, int]:
    """Return (hour, minute) after adding `minutes` to a 'HH:MM' string."""
    h, m = map(int, hhmm.split(":"))
    total = h * 60 + m + minutes
    return total // 60, total % 60
