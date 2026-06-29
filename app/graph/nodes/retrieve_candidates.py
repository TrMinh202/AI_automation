from typing import Callable

from app.clients.qdrant_client import QdrantClientWrapper
from app.schemas.graph_state import PipelineState

RETRIEVE_TOP_K = 5


def make_retrieve_candidates_node(qdrant_client: QdrantClientWrapper) -> Callable[[PipelineState], dict]:
    def node(state: PipelineState) -> dict:
        hits = qdrant_client.search(vector=state["requirement_embedding"], limit=RETRIEVE_TOP_K)
        return {"_raw_hits": hits}

    return node
