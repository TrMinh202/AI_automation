from abc import ABC, abstractmethod
from typing import ClassVar, TypedDict

from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestCase, TestStep


class TestCaseSkeleton(TypedDict):
    title: str
    preconditions: list[str]
    steps: list[TestStep]
    final_expected_result: str


class DomainRuleSet(ABC):
    domain_name: ClassVar[str]

    @abstractmethod
    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        """Sinh testcase khung (precondition/step/expected) thuan deterministic, khong goi LLM."""
        raise NotImplementedError

    def find_missing_conditions(self, req: StructuredRequirement, existing: TestCase) -> list[str]:
        existing_text = " ".join(
            [existing.title, *existing.preconditions, *(s.action + " " + s.expected_result for s in existing.steps)]
        ).lower()

        missing: list[str] = []
        for label, value in (
            ("trigger", req.trigger),
            ("vehicle_status", req.vehicle_status),
        ):
            tokens = [t for t in value.lower().split() if len(t) > 2]
            if tokens and not any(t in existing_text for t in tokens):
                missing.append(f"Additional condition from new requirement ({label}): {value}")
        return missing
