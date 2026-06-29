from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.clients.gemini_client import GeminiClient
from app.clients.qdrant_client import QdrantClientWrapper
from app.graph.builder import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    gemini_client = GeminiClient()
    qdrant_client = QdrantClientWrapper()
    qdrant_client.ensure_collection()

    app.state.gemini_client = gemini_client
    app.state.qdrant_client = qdrant_client
    app.state.graph = build_graph(gemini_client, qdrant_client)

    yield


app = FastAPI(title="Automotive Test Case Generator", lifespan=lifespan)
app.include_router(router)
