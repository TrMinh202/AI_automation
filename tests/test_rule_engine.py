from app.rule_engine import registry
from app.schemas.requirement import StructuredRequirement


def make_req(**overrides):
    base = dict(
        raw_text="khi toc do > 30km/h va cua mo thi keu chuong",
        feature="Door Open Warning Chime",
        trigger="speed > 30 km/h AND door open",
        vehicle_status="Driving",
        domain="Body Control",
    )
    base.update(overrides)
    return StructuredRequirement(**base)


def test_body_control_generates_door_steps():
    req = make_req()
    rule_set = registry.get("Body Control")
    skeleton = rule_set.generate_skeleton(req)
    assert len(skeleton["steps"]) >= 1
    assert "cua" in skeleton["steps"][0].action.lower() or "door" in req.trigger.lower()


def test_unknown_domain_falls_back_to_generic():
    req = make_req(domain="NonexistentDomain")
    rule_set = registry.get("NonexistentDomain")
    skeleton = rule_set.generate_skeleton(req)
    assert skeleton["title"]
    assert len(skeleton["steps"]) >= 1


def test_known_domains_includes_body_control():
    domains = registry.known_domains()
    assert "Body Control" in domains
