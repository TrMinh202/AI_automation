from app.rule_engine import registry
from app.schemas.graph_state import PipelineState
from app.schemas.testcase import TestCase, TestStep


def _normalize(text: str) -> str:
    return text.strip().lower()


def merge_partial_match_node(state: PipelineState) -> dict:
    req = state["structured_requirement"]
    coverage = state["coverage_result"]
    best = coverage.best_match
    base_payload = best.payload

    base_preconditions = list(base_payload.get("preconditions", []))
    base_steps = [TestStep(**s) for s in base_payload.get("steps", [])]

    rule_set = registry.get(req.domain)
    skeleton = rule_set.generate_skeleton(req)

    merged_preconditions = list(base_preconditions)
    seen_preconditions = {_normalize(p) for p in merged_preconditions}
    for p in skeleton["preconditions"]:
        if _normalize(p) not in seen_preconditions:
            merged_preconditions.append(p)
            seen_preconditions.add(_normalize(p))

    merged_steps = list(base_steps)
    seen_actions = {_normalize(s.action) for s in merged_steps}
    next_step_number = len(merged_steps) + 1
    for s in skeleton["steps"]:
        if _normalize(s.action) not in seen_actions:
            merged_steps.append(TestStep(step_number=next_step_number, action=s.action, expected_result=s.expected_result))
            seen_actions.add(_normalize(s.action))
            next_step_number += 1

    base_expected = str(base_payload.get("final_expected_result", "")).strip()
    rule_expected = skeleton["final_expected_result"].strip()
    if base_expected and rule_expected and _normalize(base_expected) != _normalize(rule_expected):
        final_expected_result = f"{base_expected} Supplemented with: {rule_expected}"
    else:
        final_expected_result = base_expected or rule_expected

    testcase = TestCase(
        testcase_id="",
        title=base_payload.get("title") or skeleton["title"],
        domain=req.domain,
        preconditions=merged_preconditions,
        steps=merged_steps,
        final_expected_result=final_expected_result,
        source_requirement=req.raw_text,
        derived_from_testcase_id=best.qdrant_point_id,
        coverage_classification=coverage.classification,
        coverage_score=coverage.final_score,
        generation_path="merge",
    )

    return {"draft_testcase": testcase}
