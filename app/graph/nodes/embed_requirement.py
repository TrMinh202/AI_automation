from typing import Callable

from app.clients.gemini_client import GeminiClient
from app.ingestion.build_payload import build_embedding_text
from app.schemas.graph_state import PipelineState


def make_embed_requirement_node(gemini_client: GeminiClient) -> Callable[[PipelineState], dict]:
    def node(state: PipelineState) -> dict:
        req = state["structured_requirement"]
        text = build_embedding_text(
            {
                "feature": req.feature,
                "trigger": req.trigger,
                "vehicle_status": req.vehicle_status,
                "domain": req.domain,
                "title": req.description or "",
                "steps": [],
            }
        )
        embedding = gemini_client.embed(text)
        return {"requirement_embedding": embedding}

    return node
