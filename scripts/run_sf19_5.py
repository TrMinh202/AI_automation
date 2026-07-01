"""
Chạy pipeline generate test case cho SF-19-5 Auto Speed Lock.
Kết quả lưu vào outputs/SF19_5_auto_speed_lock.xlsx

Usage:
    python scripts/run_sf19_5.py
"""
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

REQUIREMENT = """SF-19-5 Auto Speed Lock — Body Control Module (BCM)

Feature: The BCM shall automatically lock all doors when the vehicle speed reaches or exceeds 15 km/h, provided all doors are closed and the central lock is in the unlocked state.

Applicable vehicle state: ON (Driver Present / Ready) only.

Activation conditions (ALL must be satisfied):
1. All doors are closed: BCM sends BCM_STAT_DriverDoor=0 "Closed", BCM_STAT_PassDoor=0 "Closed", BCM_STS_TailDoor=0 "Closed".
2. Vehicle speed signal is valid and speed >= 15 km/h: ABS_VehSpd >= 15 km/h AND ABS_VehSpdValid=1 "Valid".
3. Central lock is in unlocked state: BCM sends STAT_DoorUnLockFL=1 "Unlocked".

Function output when triggered:
- BCM drives all doors to locked state and sends STAT_DoorLockFL=1 "Locked".
- BCM activates the central lock working indicator light: BCM_Doorlock_ledlight_Sts=1 "ON".
- While auto-lock is active, the door unlock function (excluding central lock switch) is blocked.

Deactivation conditions (ANY one is sufficient):
- Vehicle speed drops below 15 km/h: ABS_VehSpd < 15 km/h.
- ABS speed signal becomes invalid: ABS_VehSpdValid=0 or ABS_VehSpd signal lost (defaults to 0).
- Vehicle is already in locked state: STAT_DoorUnLockFL=0 "Locked".

Edge case — door not properly closed:
- If any door is not properly closed and vehicle speed increases above 15 km/h, the system shall NOT lock.
- When the door is closed again while speed is still >= 15 km/h, the BCM shall immediately trigger locking.

Default speed threshold: 15 km/h (BCM default)."""


async def main():
    from app.clients.gemini_client import GeminiClient
    from app.clients.qdrant_client import QdrantClientWrapper
    from app.config import settings
    from app.graph.builder import build_graph
    from app.schemas.testcase import TestCaseResult
    from app.utils.excel_exporter import build_excel

    gemini  = GeminiClient()
    qdrant  = QdrantClientWrapper(settings.qdrant_collection_name)
    bcm     = QdrantClientWrapper(settings.bcm_collection_name)
    qdrant.ensure_collection()

    graph = build_graph(gemini, qdrant, bcm)

    print("\n--- Decomposing requirement into scenarios ---")
    scenarios = gemini.decompose_to_scenarios(REQUIREMENT)
    for i, s in enumerate(scenarios, 1):
        print(f"  {i}. {s[:100]}...")

    print(f"\n--- Running pipeline for {len(scenarios)} scenario(s) ---")

    async def run_one(scenario: str) -> TestCaseResult:
        state = await graph.ainvoke({"raw_requirement_text": scenario, "errors": []})
        return TestCaseResult(
            scenario_text=scenario,
            testcase=state["final_testcase"],
            coverage=state["coverage_result"],
        )

    results = await asyncio.gather(*[run_one(s) for s in scenarios])

    print("\n--- Test cases generated ---")
    for r in results:
        tc = r.testcase
        print(f"  [{tc.testcase_id}] {tc.title}  ({tc.coverage_classification}, score={tc.coverage_score:.1f})")
        for step in tc.steps:
            print(f"    Step {step.step_number}: {step.action[:80]}")

    xlsx = build_excel(list(results))
    out_path = Path("outputs/SF19_5_auto_speed_lock.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(xlsx)
    print(f"\nSaved -> {out_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
