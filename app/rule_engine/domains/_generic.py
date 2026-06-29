from app.rule_engine.base import DomainRuleSet, TestCaseSkeleton
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestStep


class GenericRuleSet(DomainRuleSet):
    domain_name = "Generic"

    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        return TestCaseSkeleton(
            title=f"Kiem tra: {req.feature}",
            preconditions=[f"He thong da khoi dong, trang thai xe: {req.vehicle_status}"],
            steps=[
                TestStep(
                    step_number=1,
                    action=f"Ap dung dieu kien kich hoat: {req.trigger}",
                    expected_result=f"He thong phan hoi dung theo requirement: {req.description or req.raw_text}",
                )
            ],
            final_expected_result=f"He thong hoat dong dung voi requirement: {req.description or req.raw_text}",
        )
