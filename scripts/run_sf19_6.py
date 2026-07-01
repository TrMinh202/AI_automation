"""
Chay pipeline generate test case cho SF-19-6 Auto-relock.
Ket qua luu vao outputs/SF19_6_auto_relock.xlsx
"""
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

REQUIREMENT = """SF-19-6 Auto-relock — Body Control Module (BCM)

Feature: When the mechanical key unlock button is triggered, the BCM starts a 30-second timer.
If, during the 30-second countdown, no door is opened (no door status signal transitions to open state)
AND the mechanical key lock button is NOT triggered, then at the end of the 30 seconds the BCM
shall automatically drive the door lock motor to re-lock all doors.

Applicable vehicle state: ASLEEP or OFF only (Vehicle sleep / awaken states).
NOT applicable in ACC, ON (Driver Present), or ON (Ready) states.

Preconditions:
- No door is currently open: all door status signals remain closed throughout the 30s timer.
- No change in vehicle power state during the 30s timer.

Trigger (input):
- Mechanical key unlock button is triggered (user presses unlock on physical key).
- BCM starts 30-second countdown immediately upon unlock trigger.

Automatic re-lock output (triggered at end of 30s if conditions met):
- BCM drives the door lock motor to lock all doors.
- BCM sends STAT_DoorLockFL=1 "Locked".

Cancellation conditions (re-lock is NOT performed if ANY of the following occur during 30s):
- Any door is opened: door status signal changes to open state.
- Mechanical key lock button is triggered during the 30s timer.

Summary of scenarios to test:
1. Happy path: mechanical key unlocks, no door opened, no lock button pressed within 30s → BCM auto-relocks at t=30s, STAT_DoorLockFL=1.
2. Door opened during timer: mechanical key unlocks, user opens door within 30s → BCM does NOT auto-relock.
3. Manual re-lock during timer: mechanical key unlocks, user presses lock button within 30s → BCM does NOT auto-relock at t=30s (already locked).
4. Power state change during timer: vehicle power state changes during 30s → auto-relock function is cancelled.
5. Feature not applicable: vehicle in ON state → mechanical key unlock does NOT start auto-relock timer."""


async def main():
    from app.clients.gemini_client import GeminiClient
    from app.clients.qdrant_client import QdrantClientWrapper
    from app.config import settings
    from app.graph.builder import build_graph
    from app.schemas.testcase import TestCaseResult
    from app.utils.excel_exporter import build_excel

    gemini = GeminiClient()
    qdrant = QdrantClientWrapper(settings.qdrant_collection_name)
    bcm    = QdrantClientWrapper(settings.bcm_collection_name)
    qdrant.ensure_collection()

    graph = build_graph(gemini, qdrant, bcm)

    print("\n--- Decomposing SF-19-6 into scenarios ---")
    scenarios = gemini.decompose_to_scenarios(REQUIREMENT)
    for i, s in enumerate(scenarios, 1):
        print(f"  {i}. {s[:110]}")

    print(f"\n--- Running pipeline for {len(scenarios)} scenario(s) ---")

    async def run_one(scenario: str) -> TestCaseResult:
        state = await graph.ainvoke({"raw_requirement_text": scenario, "errors": []})
        tc = state["final_testcase"]
        errs = state.get("errors", [])
        if errs:
            print(f"  [WARN] {tc.testcase_id}: {errs}")
        return TestCaseResult(
            scenario_text=scenario,
            testcase=tc,
            coverage=state["coverage_result"],
        )

    results = await asyncio.gather(*[run_one(s) for s in scenarios])

    print("\n--- Test cases generated ---")
    for r in results:
        tc = r.testcase
        print(f"  [{tc.testcase_id}] {tc.title}")
        print(f"    Classification: {tc.coverage_classification}  Score: {tc.coverage_score:.1f}  Path: {tc.generation_path}")
        for step in tc.steps:
            print(f"    Step {step.step_number}: {step.action[:90]}")
        print()

    xlsx = build_excel(list(results))
    out_path = Path("outputs/SF19_6_auto_relock.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(xlsx)
    print(f"Saved -> {out_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
