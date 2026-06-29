import logging

import pandas as pd

from app.ingestion.column_mapping import ColumnMapping

logger = logging.getLogger(__name__)


def load_excel(file_path: str, mapping: ColumnMapping) -> pd.DataFrame:
    df = pd.read_excel(
        file_path,
        sheet_name=mapping.sheet_name if mapping.sheet_name else 0,
        header=mapping.header_row,
        engine="openpyxl",
    )

    rename_map = {excel_header: canonical for canonical, excel_header in mapping.columns.items()}
    df = df.rename(columns=rename_map)

    for canonical in mapping.columns:
        if canonical not in df.columns:
            df[canonical] = None

    valid_rows = []
    for idx, row in df.iterrows():
        missing = [f for f in mapping.required_fields if pd.isna(row.get(f)) or str(row.get(f)).strip() == ""]
        if missing:
            logger.warning("Bo qua dong %s: thieu truong bat buoc %s", idx, missing)
            continue
        row = row.copy()
        row["_source_row_index"] = int(idx)
        valid_rows.append(row)

    if not valid_rows:
        return df.iloc[0:0]
    return pd.DataFrame(valid_rows)
