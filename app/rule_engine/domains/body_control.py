from app.rule_engine.base import DomainRuleSet, TestCaseSkeleton
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestStep
from app.utils.text_rules import extract_threshold


class BodyControlRuleSet(DomainRuleSet):
    domain_name = "Body Control"

    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        trigger_lower = req.trigger.lower()
        preconditions = [f"Xe dang o trang thai: {req.vehicle_status}"]
        steps: list[TestStep] = []

        if "door" in trigger_lower or "cua" in trigger_lower:
            preconditions.append("Cua xe ban dau dang dong")
            steps.append(
                TestStep(step_number=1, action="Mo cua xe", expected_result="He thong nhan dien trang thai cua mo")
            )

            threshold = extract_threshold(req.trigger)
            if threshold:
                value, unit = threshold
                steps.append(
                    TestStep(
                        step_number=2,
                        action=f"Tang toc do xe vuot {value} {unit} trong khi cua van mo",
                        expected_result=f"He thong kich hoat canh bao theo dung yeu cau: {req.trigger}",
                    )
                )
            else:
                steps.append(
                    TestStep(
                        step_number=2,
                        action="Duy tri trang thai cua mo",
                        expected_result=f"He thong kich hoat phan hoi theo yeu cau: {req.feature}",
                    )
                )
        elif "window" in trigger_lower or "kinh" in trigger_lower or "cua kinh" in trigger_lower:
            steps.append(
                TestStep(
                    step_number=1,
                    action="Dieu khien cua kinh dong/mo theo dieu kien trong requirement",
                    expected_result=f"He thong phan hoi dung theo: {req.trigger}",
                )
            )
            if "obstacle" in trigger_lower or "pinch" in trigger_lower or "vat can" in trigger_lower:
                steps.append(
                    TestStep(
                        step_number=2,
                        action="Dat vat can vao duong di cua kinh khi dang dong",
                        expected_result="He thong dao chieu chong ket (anti-pinch) va dung dong kinh",
                    )
                )
        else:
            steps.append(
                TestStep(
                    step_number=1,
                    action=f"Ap dung dieu kien kich hoat: {req.trigger}",
                    expected_result=f"He thong phan hoi dung theo requirement: {req.feature}",
                )
            )

        return TestCaseSkeleton(
            title=f"Kiem tra {req.feature} ({self.domain_name})",
            preconditions=preconditions,
            steps=steps,
            final_expected_result=f"He thong hoat dong dung voi requirement: {req.description or req.raw_text}",
        )
