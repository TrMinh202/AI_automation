from typing import Optional

import yaml
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    sheet_name: Optional[str] = None
    header_row: int = 0
    columns: dict[str, str]
    required_fields: list[str] = ["domain", "title"]
    list_delimiter: str = "\n"
    # Khi dat, dung regex nay de split steps_action va steps_expected thay vi list_delimiter.
    # Vi du: "\\n(?=\\d+\\.)" de split theo boundary "1." "2." "3." ...
    step_split_regex: Optional[str] = None


def load_column_mapping(path: str = "config/column_mapping.yaml") -> ColumnMapping:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ColumnMapping(**raw)
