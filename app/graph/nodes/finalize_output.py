import uuid

from app.schemas.graph_state import PipelineState

_DOMAIN_PREFIX_MAX_LEN = 3


def finalize_output_node(state: PipelineState) -> dict:
    testcase = state["draft_testcase"]
    domain_prefix = "".join(c for c in testcase.domain.upper() if c.isalnum())[:_DOMAIN_PREFIX_MAX_LEN] or "GEN"
    testcase.testcase_id = f"TC-{domain_prefix}-{uuid.uuid4().hex[:8]}"
    return {"final_testcase": testcase}
