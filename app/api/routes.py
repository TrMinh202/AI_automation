import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.dependencies import get_compiled_graph, get_gemini_client, get_qdrant_client
from app.schemas.requirement import GenerateTestCaseRequest
from app.schemas.testcase import GenerateTestCasesResponse, TestCaseResult
from app.utils.excel_exporter import build_excel

OUTPUT_DIR = Path("outputs")

router = APIRouter()


async def _run_pipeline(graph, scenario_text: str) -> TestCaseResult:
    initial_state = {"raw_requirement_text": scenario_text, "errors": []}
    result_state = await graph.ainvoke(initial_state)
    return TestCaseResult(
        scenario_text=scenario_text,
        testcase=result_state["final_testcase"],
        coverage=result_state["coverage_result"],
    )


@router.post("/testcases/generate", response_model=GenerateTestCasesResponse)
async def generate_testcases(
    req: GenerateTestCaseRequest,
    graph=Depends(get_compiled_graph),
    gemini_client=Depends(get_gemini_client),
):
    scenarios = gemini_client.decompose_to_scenarios(req.requirement_text)
    results = await asyncio.gather(*[_run_pipeline(graph, s) for s in scenarios])
    return GenerateTestCasesResponse(testcases=list(results), total_count=len(results))


@router.post("/testcases/generate/export")
async def export_testcases(
    req: GenerateTestCaseRequest,
    graph=Depends(get_compiled_graph),
    gemini_client=Depends(get_gemini_client),
):
    scenarios = gemini_client.decompose_to_scenarios(req.requirement_text)
    results   = await asyncio.gather(*[_run_pipeline(graph, s) for s in scenarios])
    xlsx_bytes = build_excel(list(results))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"testcases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    (OUTPUT_DIR / filename).write_bytes(xlsx_bytes)

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/health")
async def health(qdrant_client=Depends(get_qdrant_client)):
    qdrant_ok = qdrant_client.is_healthy()
    return {"status": "ok" if qdrant_ok else "degraded", "qdrant": qdrant_ok}
