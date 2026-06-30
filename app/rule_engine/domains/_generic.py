from app.rule_engine.base import DomainRuleSet, TestCaseSkeleton
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestStep


class GenericRuleSet(DomainRuleSet):
    domain_name = "Generic"

    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        return TestCaseSkeleton(
            title=f"Verify: {req.feature}",
            preconditions=[f"System initialized, vehicle state: {req.vehicle_status}"],
            steps=[
                TestStep(
                    step_number=1,
                    action=f"Apply activation condition: {req.trigger}",
                    expected_result=f"System responds correctly per requirement: {req.description or req.raw_text}",
                )
            ],
            final_expected_result=f"System operates correctly per requirement: {req.description or req.raw_text}",
        )
