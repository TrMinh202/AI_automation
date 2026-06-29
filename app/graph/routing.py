from typing import Literal

from app.schemas.graph_state import PipelineState

BranchName = Literal["reuse_high_match", "merge_partial_match", "generate_from_rules"]


def route_by_coverage(state: PipelineState) -> BranchName:
    score = state["coverage_result"].final_score
    if score > 90:
        return "reuse_high_match"
    if score >= 50:
        return "merge_partial_match"
    return "generate_from_rules"
