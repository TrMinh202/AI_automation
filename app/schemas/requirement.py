from typing import Optional

from pydantic import BaseModel, Field


class StructuredRequirement(BaseModel):
    raw_text: str
    feature: str
    trigger: str
    vehicle_status: str
    domain: str
    description: Optional[str] = Field(
        default=None,
        description="Ban tom tat ngan gon, chuan hoa cua requirement, dung de embedding va LLM refine.",
    )
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class GenerateTestCaseRequest(BaseModel):
    requirement_text: str
