import pytest
from pydantic import ValidationError

from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestCase, TestStep


def test_structured_requirement_valid():
    req = StructuredRequirement(
        raw_text="khi toc do > 30km/h va cua mo thi keu chuong",
        feature="Door Open Warning Chime",
        trigger="speed > 30 km/h AND door open",
        vehicle_status="Driving",
        domain="Body Control",
    )
    assert req.feature == "Door Open Warning Chime"


def test_structured_requirement_missing_field_raises():
    with pytest.raises(ValidationError):
        StructuredRequirement(raw_text="abc", feature="x")


def test_testcase_valid():
    tc = TestCase(
        testcase_id="TC-BC-1234",
        title="Test door warning",
        domain="Body Control",
        preconditions=["Xe dang chay"],
        steps=[TestStep(step_number=1, action="Mo cua", expected_result="Canh bao")],
        final_expected_result="He thong canh bao dung",
        source_requirement="raw text",
        coverage_classification="New",
        coverage_score=10.0,
        generation_path="rule_only",
    )
    assert tc.steps[0].step_number == 1


def test_testcase_invalid_classification_raises():
    with pytest.raises(ValidationError):
        TestCase(
            testcase_id="TC-1",
            title="t",
            domain="d",
            final_expected_result="x",
            source_requirement="x",
            coverage_classification="Invalid",
            coverage_score=1.0,
            generation_path="rule_only",
        )
