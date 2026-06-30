from app.rule_engine.base import DomainRuleSet, TestCaseSkeleton
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestStep
from app.utils.text_rules import extract_threshold


class BodyControlRuleSet(DomainRuleSet):
    domain_name = "Body Control"

    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        trigger_lower = req.trigger.lower()
        preconditions = [f"Vehicle is in state: {req.vehicle_status}"]
        steps: list[TestStep] = []

        if "door" in trigger_lower or "cua" in trigger_lower:
            preconditions.append("Vehicle door is initially closed")
            steps.append(
                TestStep(step_number=1, action="Open the vehicle door", expected_result="System detects door-open state")
            )

            threshold = extract_threshold(req.trigger)
            if threshold:
                value, unit = threshold
                steps.append(
                    TestStep(
                        step_number=2,
                        action=f"Accelerate vehicle beyond {value} {unit} while door remains open",
                        expected_result=f"System activates warning as required: {req.trigger}",
                    )
                )
            else:
                steps.append(
                    TestStep(
                        step_number=2,
                        action="Maintain door-open state",
                        expected_result=f"System activates response as required: {req.feature}",
                    )
                )
        elif "window" in trigger_lower or "kinh" in trigger_lower or "cua kinh" in trigger_lower:
            steps.append(
                TestStep(
                    step_number=1,
                    action="Control window open/close per condition in requirement",
                    expected_result=f"System responds correctly per: {req.trigger}",
                )
            )
            if "obstacle" in trigger_lower or "pinch" in trigger_lower or "vat can" in trigger_lower:
                steps.append(
                    TestStep(
                        step_number=2,
                        action="Place an obstacle in the window path while closing",
                        expected_result="System reverses direction (anti-pinch) and stops closing",
                    )
                )
        else:
            steps.append(
                TestStep(
                    step_number=1,
                    action=f"Apply activation condition: {req.trigger}",
                    expected_result=f"System responds correctly per requirement: {req.feature}",
                )
            )

        return TestCaseSkeleton(
            title=f"Verify {req.feature} ({self.domain_name})",
            preconditions=preconditions,
            steps=steps,
            final_expected_result=f"System operates correctly per requirement: {req.description or req.raw_text}",
        )
