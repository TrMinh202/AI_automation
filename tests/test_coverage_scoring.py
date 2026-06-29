from app.schemas.requirement import StructuredRequirement
from app.utils.similarity import classify_score, combined_score, field_match_score


def make_req(**overrides):
    base = dict(
        raw_text="raw",
        feature="Door Open Warning Chime",
        trigger="speed > 30 km/h AND door open",
        vehicle_status="Driving",
        domain="Body Control",
    )
    base.update(overrides)
    return StructuredRequirement(**base)


def test_field_match_score_exact_match_is_one():
    req = make_req()
    payload = {
        "feature": "Door Open Warning Chime",
        "trigger": "speed > 30 km/h AND door open",
        "vehicle_status": "Driving",
        "domain": "Body Control",
    }
    score = field_match_score(req, payload)
    assert score == 1.0


def test_field_match_score_no_overlap_is_zero():
    req = make_req()
    payload = {
        "feature": "Completely Unrelated",
        "trigger": "totally different",
        "vehicle_status": "Parked",
        "domain": "Powertrain",
    }
    score = field_match_score(req, payload)
    assert score == 0.0


def test_combined_score_formula():
    assert combined_score(1.0, 1.0) == 100.0
    assert combined_score(0.0, 0.0) == 0.0
    assert combined_score(0.5, 0.5) == 50.0


def test_classify_score_boundaries():
    assert classify_score(95) == "Giống nhiều"
    assert classify_score(90) == "Giống một phần"
    assert classify_score(90.01) == "Giống nhiều"
    assert classify_score(50) == "Giống một phần"
    assert classify_score(49.99) == "Mới hoàn toàn"
    assert classify_score(0) == "Mới hoàn toàn"
