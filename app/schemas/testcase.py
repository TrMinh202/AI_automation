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
    coverage_classification: Literal["Giống nhiều", "Giống một phần", "Mới hoàn toàn"]
    coverage_score: float
    generation_path: Literal["reuse", "merge", "rule_only"]


class GenerateTestCaseResponse(BaseModel):
    testcase: TestCase
    coverage: "CoverageScoreResult"


from app.schemas.coverage import CoverageScoreResult  # noqa: E402

GenerateTestCaseResponse.model_rebuild()
