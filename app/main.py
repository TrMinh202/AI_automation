from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.clients.gemini_client import GeminiClient
from app.clients.qdrant_client import QdrantClientWrapper
from app.config import settings
from app.graph.builder import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    gemini_client  = GeminiClient()
    qdrant_client  = QdrantClientWrapper(settings.qdrant_collection_name)
    bcm_client     = QdrantClientWrapper(settings.bcm_collection_name)

    qdrant_client.ensure_collection()
    # BCM collection is created on-demand during ingestion; no need to ensure here.

    app.state.gemini_client = gemini_client
    app.state.qdrant_client = qdrant_client
    app.state.bcm_client    = bcm_client
    app.state.graph         = build_graph(gemini_client, qdrant_client, bcm_client)

    yield


app = FastAPI(title="Automotive Test Case Generator", lifespan=lifespan)
app.include_router(router)
