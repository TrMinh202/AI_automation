from typing import Literal, Optional

from pydantic import BaseModel


class MatchedCandidate(BaseModel):
    qdrant_point_id: str
    cosine_similarity: float
    field_match_score: float
    combined_score: float
    payload: dict


class CoverageScoreResult(BaseModel):
    best_match: Optional[MatchedCandidate] = None
    top_k_matches: list[MatchedCandidate] = []
    final_score: float
    classification: Literal["High Match", "Partial Match", "New"]
