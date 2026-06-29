from app.rule_engine.base import DomainRuleSet, TestCaseSkeleton
from app.rule_engine.domains._generic import GenericRuleSet
from app.schemas.requirement import StructuredRequirement


class PowertrainRuleSet(DomainRuleSet):
    """Stub: dung logic generic, bo sung rule rieng cho Powertrain (vi du dong co, hop so) sau."""

    domain_name = "Powertrain"
    _fallback = GenericRuleSet()

    def generate_skeleton(self, req: StructuredRequirement) -> TestCaseSkeleton:
        return self._fallback.generate_skeleton(req)
