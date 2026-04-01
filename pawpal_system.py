"""
PawPal+ — core backend logic.
Classes: Task, Pet, Owner, Scheduler.
"""

from dataclasses import dataclass, field
from typing import Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """Represents a single pet care activity with time, priority, and completion state."""

    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str = ""      # e.g. "feeding", "exercise", "grooming", "medication"
    completed: bool = False

    def is_doable(self, budget: int) -> bool:
        """Return True if this task fits within the remaining time budget (minutes)."""
        return self.duration_minutes <= budget

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def describe(self) -> str:
        """Return a human-readable one-line description of the task."""
        status = "done" if self.completed else "pending"
        cat = f" [{self.category}]" if self.category else ""
        return f"{self.title}{cat} — {self.duration_minutes} min | priority: {self.priority} | {status}"


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
        pairs = []
        for pet in self._pets:
            for task in pet.get_tasks():
                pairs.append((pet, task))
        return pairs


@dataclass
class Scheduler:
    """Retrieves tasks from an Owner's pets and builds a prioritized daily plan."""

    owner: Owner
    pet: Pet
    time_budget: Optional[int] = None   # defaults to owner.available_minutes if None

    def _effective_budget(self) -> int:
        """Return the active time budget in minutes."""
        return self.time_budget if self.time_budget is not None else self.owner.available_minutes

    def build_plan(self) -> list[Task]:
        """
        Select tasks for the pet that fit within the time budget.
        Tasks are ordered high → medium → low priority.
        Within the same priority, shorter tasks are preferred.
        Returns the list of scheduled Task objects.
        """
        candidates = sorted(
            self.pet.get_tasks(),
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )
        budget = self._effective_budget()
        plan: list[Task] = []
        for task in candidates:
            if task.is_doable(budget):
                plan.append(task)
                budget -= task.duration_minutes
        return plan

    def explain_plan(self) -> str:
        """
        Return a plain-English explanation of the generated plan,
        showing each task's time slot and the reason it was chosen.
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
            start = elapsed
            end = elapsed + task.duration_minutes
            reason = "high priority" if task.priority == "high" else f"{task.priority} priority"
            lines.append(f"  {i}. [{start:>3}–{end:<3} min] {task.title}  ({reason})")
            elapsed = end

        lines.append(f"\nTotal time used: {elapsed} min / {self._effective_budget()} min available.")
        return "\n".join(lines)
