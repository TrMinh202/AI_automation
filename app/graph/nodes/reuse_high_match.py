from app.rule_engine import registry
from app.schemas.graph_state import PipelineState
from app.schemas.testcase import TestCase, TestStep


def reuse_high_match_node(state: PipelineState) -> dict:
    req = state["structured_requirement"]
    coverage = state["coverage_result"]
    best = coverage.best_match
    payload = best.payload

    steps = [TestStep(**s) for s in payload.get("steps", [])]
    preconditions = list(payload.get("preconditions", []))

    testcase = TestCase(
        testcase_id="",
        title=payload.get("title", req.feature),
        domain=req.domain,
        preconditions=preconditions,
        steps=steps,
        final_expected_result=payload.get("final_expected_result", ""),
        source_requirement=req.raw_text,
        derived_from_testcase_id=best.qdrant_point_id,
        coverage_classification=coverage.classification,
        coverage_score=coverage.final_score,
        generation_path="reuse",
    )

    rule_set = registry.get(req.domain)
    missing_conditions = rule_set.find_missing_conditions(req, testcase)
    if missing_conditions:
        testcase.preconditions.extend(missing_conditions)

    return {"draft_testcase": testcase}
