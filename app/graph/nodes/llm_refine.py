from typing import Callable

from app.clients.gemini_client import GeminiClient
from app.schemas.graph_state import PipelineState
from app.schemas.testcase import TestCase


def _is_structurally_valid(draft: TestCase, refined: TestCase) -> bool:
    if len(draft.steps) != len(refined.steps):
        return False
    if [s.step_number for s in draft.steps] != [s.step_number for s in refined.steps]:
        return False
    if len(draft.preconditions) != len(refined.preconditions):
        return False
    if draft.domain != refined.domain:
        return False
    if draft.derived_from_testcase_id != refined.derived_from_testcase_id:
        return False
    if draft.coverage_classification != refined.coverage_classification:
        return False
    if draft.generation_path != refined.generation_path:
        return False
    return True


def make_llm_refine_node(gemini_client: GeminiClient) -> Callable[[PipelineState], dict]:
    def node(state: PipelineState) -> dict:
        draft      = state["draft_testcase"]
        req        = state["structured_requirement"]
        bcm_ctx    = state.get("bcm_context") or []
        errors     = list(state.get("errors", []))

        try:
            refined = gemini_client.refine_wording(draft, req, bcm_context=bcm_ctx)
        except Exception as exc:
            errors.append(f"llm_refine failed: {exc}")
            return {"draft_testcase": draft, "errors": errors}

        if not _is_structurally_valid(draft, refined):
            errors.append("llm_refine vi pham cau truc, fallback ve draft_testcase goc")
            return {"draft_testcase": draft, "errors": errors}

        refined.testcase_id               = draft.testcase_id
        refined.derived_from_testcase_id  = draft.derived_from_testcase_id
        refined.coverage_classification   = draft.coverage_classification
        refined.coverage_score            = draft.coverage_score
        refined.generation_path           = draft.generation_path
        refined.source_requirement        = draft.source_requirement
        refined.domain                    = draft.domain

        return {"draft_testcase": refined, "errors": errors}

    return node
