"""
Retrieve relevant BCM/spec chunks from Qdrant to provide technical reference
context for test case generation and refinement.

Gracefully returns an empty list if the BCM collection does not exist yet,
so the pipeline still works before any BCM documents are ingested.
"""
import logging
from typing import Callable

from app.clients.qdrant_client import QdrantClientWrapper
from app.schemas.graph_state import PipelineState

logger = logging.getLogger(__name__)

BCM_RETRIEVE_TOP_K = 4
BCM_MAX_CHARS_PER_CHUNK = 800


def make_retrieve_bcm_context_node(
    bcm_client: QdrantClientWrapper,
) -> Callable[[PipelineState], dict]:
    def node(state: PipelineState) -> dict:
        if not bcm_client.collection_exists():
            logger.debug("BCM collection '%s' not found — skipping BCM context retrieval", bcm_client.collection_name)
            return {"bcm_context": []}

        try:
            hits = bcm_client.search(
                vector=state["requirement_embedding"],
                limit=BCM_RETRIEVE_TOP_K,
            )
            chunks = []
            for hit in hits:
                text = hit.payload.get("text", "").strip()
                if text:
                    # Truncate very long chunks to keep prompt size manageable
                    chunks.append(text[:BCM_MAX_CHARS_PER_CHUNK])
            return {"bcm_context": chunks}
        except Exception as exc:
            logger.warning("BCM context retrieval failed: %s", exc)
            return {"bcm_context": []}

    return node
