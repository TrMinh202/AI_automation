from typing import Callable

from app.clients.gemini_client import GeminiClient
from app.schemas.graph_state import PipelineState


def make_parse_requirement_node(gemini_client: GeminiClient) -> Callable[[PipelineState], dict]:
    def node(state: PipelineState) -> dict:
        structured = gemini_client.parse_to_structured(state["raw_requirement_text"])
        return {"structured_requirement": structured}

    return node
