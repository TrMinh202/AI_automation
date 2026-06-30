import hashlib
import json
import re
import uuid

import pandas as pd
from qdrant_client.http.models import PointStruct


def parse_list_cell(cell_value, delimiter: str, regex_pattern: str | None = None) -> list[str]:
    if cell_value is None or (isinstance(cell_value, float) and pd.isna(cell_value)):
        return []
    text = str(cell_value)
    if regex_pattern:
        return [part.strip() for part in re.split(regex_pattern, text) if part.strip()]
    return [part.strip() for part in text.split(delimiter) if part.strip()]


def build_steps(actions: list[str], expecteds: list[str]) -> list[dict]:
    length = max(len(actions), len(expecteds))
    actions = actions + [""] * (length - len(actions))
    expecteds = expecteds + [""] * (length - len(expecteds))
    return [
        {"step_number": i + 1, "action": actions[i], "expected_result": expecteds[i]}
        for i in range(length)
    ]


def build_embedding_text(row: dict) -> str:
    steps_text = " ".join(f"{s['action']} {s['expected_result']}" for s in row.get("steps", []))
    parts = [
        str(row.get("feature", "")),
        str(row.get("trigger", "")),
        str(row.get("vehicle_status", "")),
        str(row.get("domain", "")),
        str(row.get("title", "")),
        str(row.get("final_expected_result", "")),
        steps_text,
    ]
    return " | ".join(p for p in parts if p and p != "nan")


def stable_point_id(source_file: str, row_index: int) -> str:
    digest = hashlib.sha256(f"{source_file}:{row_index}".encode("utf-8")).hexdigest()
    return str(uuid.UUID(hex=digest[:32]))


def build_point(
    row: dict,
    row_index: int,
    source_file: str,
    sheet_name: str,
    embedding: list[float],
) -> PointStruct:
    """row da duoc parse san: preconditions: list[str], steps: list[{action, expected_result}]."""
    steps = build_steps(
        [s["action"] for s in row.get("steps", [])],
        [s["expected_result"] for s in row.get("steps", [])],
    )

    payload = {
        "feature": str(row.get("feature", "")),
        "trigger": str(row.get("trigger", "")),
        "vehicle_status": str(row.get("vehicle_status", "")),
        "domain": str(row.get("domain", "")),
        "title": str(row.get("title", "")),
        "preconditions": row.get("preconditions", []),
        "steps": steps,
        "final_expected_result": str(row.get("final_expected_result", "")),
        "source_file": source_file,
        "source_row": row_index,
        "source_sheet": sheet_name,
        "raw_row_json": json.dumps(
            {k: str(v) for k, v in row.items() if k not in ("preconditions", "steps")}, ensure_ascii=False
        ),
    }

    return PointStruct(
        id=stable_point_id(source_file, row_index),
        vector=embedding,
        payload=payload,
    )
