from app.graph.routing import route_by_coverage
from app.schemas.coverage import CoverageScoreResult


def make_state(score: float):
    return {
        "coverage_result": CoverageScoreResult(
            best_match=None,
            top_k_matches=[],
            final_score=score,
            classification="Mới hoàn toàn",
        )
    }


def test_route_high_score_reuses():
    assert route_by_coverage(make_state(95)) == "reuse_high_match"


def test_route_mid_score_merges():
    assert route_by_coverage(make_state(70)) == "merge_partial_match"


def test_route_low_score_generates_from_rules():
    assert route_by_coverage(make_state(20)) == "generate_from_rules"


def test_route_boundary_90_is_merge():
    assert route_by_coverage(make_state(90)) == "merge_partial_match"


def test_route_boundary_90_01_is_reuse():
    assert route_by_coverage(make_state(90.01)) == "reuse_high_match"


def test_route_boundary_50_is_merge():
    assert route_by_coverage(make_state(50)) == "merge_partial_match"
