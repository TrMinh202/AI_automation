from fastapi import Request


def get_compiled_graph(request: Request):
    return request.app.state.graph


def get_qdrant_client(request: Request):
    return request.app.state.qdrant_client


def get_bcm_client(request: Request):
    return request.app.state.bcm_client


def get_gemini_client(request: Request):
    return request.app.state.gemini_client
