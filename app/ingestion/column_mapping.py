from typing import Optional

import yaml
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    sheet_name: Optional[str] = None
    header_row: int = 0
    columns: dict[str, str]
    required_fields: list[str] = ["feature", "trigger", "domain"]
    list_delimiter: str = "\n"


def load_column_mapping(path: str = "config/column_mapping.yaml") -> ColumnMapping:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ColumnMapping(**raw)
