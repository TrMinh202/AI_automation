from typing import Literal, Optional

from pydantic import BaseModel


class TestStep(BaseModel):
    step_number: int
    action: str
    expected_result: str


class TestCase(BaseModel):
    testcase_id: str
    title: str
    domain: str
    preconditions: list[str] = []
    steps: list[TestStep] = []
    final_expected_result: str
    source_requirement: str
    derived_from_testcase_id: Optional[str] = None
    coverage_classification: Literal["High Match", "Partial Match", "New"]
    coverage_score: float
    generation_path: Literal["reuse", "merge", "rule_only"]


class TestCaseResult(BaseModel):
    scenario_text: str
    testcase: TestCase
    coverage: "CoverageScoreResult"


class GenerateTestCasesResponse(BaseModel):
    testcases: list[TestCaseResult]
    total_count: int


# kept for backward-compat with any direct imports
class GenerateTestCaseResponse(BaseModel):
    testcase: TestCase
    coverage: "CoverageScoreResult"


from app.schemas.coverage import CoverageScoreResult  # noqa: E402

GenerateTestCaseResponse.model_rebuild()
TestCaseResult.model_rebuild()
GenerateTestCasesResponse.model_rebuild()
