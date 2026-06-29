from fastapi import APIRouter, Depends

from app.api.dependencies import get_compiled_graph, get_qdrant_client
from app.schemas.requirement import GenerateTestCaseRequest
from app.schemas.testcase import GenerateTestCaseResponse

router = APIRouter()


@router.post("/testcases/generate", response_model=GenerateTestCaseResponse)
async def generate_testcase(req: GenerateTestCaseRequest, graph=Depends(get_compiled_graph)):
    initial_state = {"raw_requirement_text": req.requirement_text, "errors": []}
    result_state = await graph.ainvoke(initial_state)
    return GenerateTestCaseResponse(
        testcase=result_state["final_testcase"],
        coverage=result_state["coverage_result"],
    )


@router.get("/health")
async def health(qdrant_client=Depends(get_qdrant_client)):
    qdrant_ok = qdrant_client.is_healthy()
    return {"status": "ok" if qdrant_ok else "degraded", "qdrant": qdrant_ok}
