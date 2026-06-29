from app.schemas.coverage import CoverageScoreResult, MatchedCandidate
from app.schemas.graph_state import PipelineState
from app.utils.similarity import classify_score, combined_score, field_match_score

MIN_COSINE_FLOOR = 0.3


def score_coverage_node(state: PipelineState) -> dict:
    req = state["structured_requirement"]
    hits = state.get("_raw_hits") or []

    candidates: list[MatchedCandidate] = []
    for hit in hits:
        cos_sim = max(0.0, min(1.0, hit.score))
        if cos_sim < MIN_COSINE_FLOOR:
            continue
        field_score = field_match_score(req, hit.payload)
        score = combined_score(cos_sim, field_score)
        candidates.append(
            MatchedCandidate(
                qdrant_point_id=str(hit.id),
                cosine_similarity=cos_sim,
                field_match_score=field_score,
                combined_score=score,
                payload=hit.payload,
            )
        )

    candidates.sort(key=lambda c: c.combined_score, reverse=True)
    best = candidates[0] if candidates else None
    final_score = best.combined_score if best else 0.0

    result = CoverageScoreResult(
        best_match=best,
        top_k_matches=candidates,
        final_score=final_score,
        classification=classify_score(final_score),
    )
    return {"coverage_result": result}
