from typing import Optional, TypedDict

from app.schemas.coverage import CoverageScoreResult
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestCase


class PipelineState(TypedDict, total=False):
    raw_requirement_text: str
    structured_requirement: Optional[StructuredRequirement]
    requirement_embedding: Optional[list[float]]
    _raw_hits: Optional[list]
    coverage_result: Optional[CoverageScoreResult]
    draft_testcase: Optional[TestCase]
    final_testcase: Optional[TestCase]
    errors: list[str]
