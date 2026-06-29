from app.rule_engine import registry
from app.schemas.graph_state import PipelineState
from app.schemas.testcase import TestCase


def generate_from_rules_node(state: PipelineState) -> dict:
    req = state["structured_requirement"]
    coverage = state["coverage_result"]

    rule_set = registry.get(req.domain)
    skeleton = rule_set.generate_skeleton(req)

    testcase = TestCase(
        testcase_id="",
        title=skeleton["title"],
        domain=req.domain,
        preconditions=skeleton["preconditions"],
        steps=skeleton["steps"],
        final_expected_result=skeleton["final_expected_result"],
        source_requirement=req.raw_text,
        derived_from_testcase_id=None,
        coverage_classification=coverage.classification,
        coverage_score=coverage.final_score,
        generation_path="rule_only",
    )

    return {"draft_testcase": testcase}
