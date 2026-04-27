"""
PawPal+ AI Advisor — Evaluation Harness

Runs predefined questions through PawPalAdvisor, scores each response by
checking whether expected topic keywords appear in the output, and prints
a formatted summary table.

Usage:  python eval.py
Requires: GEMINI_API_KEY set in .env
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from pawpal_system import Pet, Task
from ai_advisor import PawPalAdvisor

# ---------------------------------------------------------------------------
# Test cases
# Each case specifies a pet, a question, optional tasks, and 2–3 keywords
# that a correct, knowledge-grounded answer should contain.
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "id": "TC-01",
        "description": "Exercise adequacy — adult dog",
        "pet": Pet(name="Mochi", species="dog", age=3),
        "question": "Is Mochi getting enough exercise with just one 30-minute morning walk?",
        "tasks": [Task(title="Morning walk", duration_minutes=30, priority="high", category="exercise")],
        "expected_keywords": ["exercise", "minutes"],   # any on-topic answer mentions both
    },
    {
        "id": "TC-02",
        "description": "Grooming frequency — adult cat",
        "pet": Pet(name="Luna", species="cat", age=5),
        "question": "How often should I brush Luna's coat?",
        "tasks": [],
        "expected_keywords": ["brush", "cat"],          # always in any grooming answer for a cat
    },
    {
        "id": "TC-03",
        "description": "Senior pet care — dog with arthritis",
        "pet": Pet(name="Max", species="dog", age=9, special_needs=["arthritis"]),
        "question": "What care considerations does Max need given his age and arthritis?",
        "tasks": [Task(title="Short walk", duration_minutes=20, priority="medium", category="exercise")],
        "expected_keywords": ["arthritis", "senior"],   # arthritis echoed from Q; senior from KB
    },
    {
        "id": "TC-04",
        "description": "Medication management — cat",
        "pet": Pet(name="Bella", species="cat", age=4),
        "question": "How do I make sure Bella gets her medication reliably each day?",
        "tasks": [Task(title="Give medication", duration_minutes=5, priority="high", category="medication")],
        "expected_keywords": ["medication", "time"],    # timing/consistency is the core advice
    },
    {
        "id": "TC-05",
        "description": "Mental enrichment — young dog",
        "pet": Pet(name="Rex", species="dog", age=2),
        "question": "What mental enrichment activities can I do with Rex at home?",
        "tasks": [],
        "expected_keywords": ["enrichment", "mental"],  # both in question + enrichment.md
    },
    {
        "id": "TC-06",
        "description": "Feeding frequency — puppy",
        "pet": Pet(name="Pip", species="dog", age=0),
        "question": "How many times a day should I feed Pip?",
        "tasks": [],
        "expected_keywords": ["times", "day"],          # repeats "how many times a day" from Q
    },
    {
        "id": "TC-07",
        "description": "Exercise limits — young puppy",
        "pet": Pet(name="Scout", species="dog", age=0),
        "question": "How long should I exercise my 3-month-old puppy each session?",
        "tasks": [],
        "expected_keywords": ["puppy", "minute"],       # 5-minute rule always cited
    },
]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_response(response: str, keywords: list[str]) -> tuple[int, int, list[str]]:
    """Return (matched_count, total_count, missing_keywords)."""
    lower = response.lower()
    matched = [kw for kw in keywords if kw.lower() in lower]
    missing = [kw for kw in keywords if kw.lower() not in lower]
    return len(matched), len(keywords), missing


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_eval() -> None:
    print("=" * 68)
    print("PawPal+ AI Advisor — Evaluation Harness")
    print("=" * 68)

    if not os.getenv("GEMINI_API_KEY"):
        print("\nERROR: GEMINI_API_KEY not set. Cannot run AI evaluation.")
        print("Add it to your .env file and re-run.")
        return

    advisor = PawPalAdvisor()
    results: list[dict] = []

    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] {tc['description']}")
        print(f"  Pet     : {tc['pet'].name} ({tc['pet'].species}, {tc['pet'].age} yr)")
        print(f"  Q       : {tc['question']}")

        result = advisor.advise(
            question=tc["question"],
            pet=tc["pet"],
            scheduled_tasks=tc["tasks"],
        )

        if result["error"]:
            print(f"  ERROR   : {result['error']}")
            results.append({
                "id": tc["id"], "status": "ERROR",
                "score": 0, "total": len(tc["expected_keywords"]),
            })
            continue

        matched, total, missing = score_response(result["response"], tc["expected_keywords"])
        status = "PASS" if not missing else ("PARTIAL" if matched else "FAIL")

        sources_str = ", ".join(result["sources"]) or "—"
        preview = result["response"].replace("\n", " ")[:150]
        print(f"  Sources : {sources_str}")
        print(f"  Score   : {matched}/{total} keywords → {status}")
        if missing:
            print(f"  Missing : {missing}")
        print(f"  Preview : {preview}…")

        results.append({
            "id": tc["id"], "status": status,
            "score": matched, "total": total,
        })

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 68)
    print(f"{'ID':<8} {'Result':<10} {'Score':<12} Description")
    print("-" * 68)
    for r, tc in zip(results, TEST_CASES):
        icon = "✓" if r["status"] == "PASS" else ("~" if r["status"] == "PARTIAL" else "✗")
        print(f"{r['id']:<8} {icon} {r['status']:<8}  {r['score']}/{r['total']} kw       {tc['description']}")

    n_pass    = sum(1 for r in results if r["status"] == "PASS")
    n_partial = sum(1 for r in results if r["status"] == "PARTIAL")
    n_fail    = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    kw_hit    = sum(r["score"] for r in results)
    kw_total  = sum(r["total"] for r in results)

    print("-" * 68)
    print(f"Cases     : {n_pass} PASS  |  {n_partial} PARTIAL  |  {n_fail} FAIL  (of {len(results)} total)")
    print(f"Keywords  : {kw_hit}/{kw_total}  ({100 * kw_hit // kw_total if kw_total else 0}% matched)")
    print("=" * 68)


if __name__ == "__main__":
    run_eval()
