import importlib
import inspect
import pkgutil

from app.rule_engine import domains as domains_package
from app.rule_engine.base import DomainRuleSet
from app.rule_engine.domains._generic import GenericRuleSet

_registry: dict[str, DomainRuleSet] = {}
_generic = GenericRuleSet()


def _discover() -> None:
    if _registry:
        return
    for module_info in pkgutil.iter_modules(domains_package.__path__):
        name = module_info.name
        if name.startswith("_"):
            continue
        module = importlib.import_module(f"app.rule_engine.domains.{name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, DomainRuleSet) and obj is not DomainRuleSet:
                instance = obj()
                _registry[instance.domain_name.strip().lower()] = instance


def get(domain: str) -> DomainRuleSet:
    _discover()
    return _registry.get(domain.strip().lower(), _generic)


def known_domains() -> list[str]:
    _discover()
    return [rs.domain_name for rs in _registry.values()]
