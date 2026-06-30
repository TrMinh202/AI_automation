import re
from typing import Literal

from app.schemas.requirement import StructuredRequirement

_TOKEN_RE = re.compile(r"[a-zA-Z0-9À-ỹ]+")


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(a: str, b: str) -> float:
    if a.strip().lower() == b.strip().lower():
        return 1.0
    tokens_a, tokens_b = _tokenize(a), _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def field_match_score(requirement: StructuredRequirement, candidate_payload: dict) -> float:
    domain_match = 1.0 if requirement.domain.strip().lower() == str(candidate_payload.get("domain", "")).strip().lower() else 0.0
    feature_match = _jaccard(requirement.feature, str(candidate_payload.get("feature", "")))
    trigger_match = _jaccard(requirement.trigger, str(candidate_payload.get("trigger", "")))
    vehicle_status_match = _jaccard(requirement.vehicle_status, str(candidate_payload.get("vehicle_status", "")))

    return (
        0.20 * domain_match
        + 0.30 * feature_match
        + 0.30 * trigger_match
        + 0.20 * vehicle_status_match
    )


def combined_score(cosine_similarity: float, field_score: float) -> float:
    cos_sim = max(0.0, min(1.0, cosine_similarity))
    field = max(0.0, min(1.0, field_score))
    return round(100 * (0.6 * cos_sim + 0.4 * field), 2)


def classify_score(score: float) -> Literal["High Match", "Partial Match", "New"]:
    if score > 90:
        return "High Match"
    if score >= 50:
        return "Partial Match"
    return "New"
