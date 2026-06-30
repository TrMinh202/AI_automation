import io
from openpyxl import Workbook
from openpyxl.styles import (
    Alignment, Border, Font, PatternFill, Side
)
from openpyxl.utils import get_column_letter

from app.schemas.testcase import TestCaseResult

_HEADER_FILL   = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT   = Font(bold=True, color="FFFFFF", size=11)
_TC_FILL       = PatternFill("solid", fgColor="D6E4F0")
_STEP_FILL_ODD = PatternFill("solid", fgColor="EBF5FB")
_BORDER_SIDE   = Side(style="thin", color="AAAAAA")
_BORDER        = Border(
    left=_BORDER_SIDE, right=_BORDER_SIDE,
    top=_BORDER_SIDE,  bottom=_BORDER_SIDE,
)
_CENTER = Alignment(horizontal="center", vertical="top", wrap_text=True)
_LEFT   = Alignment(horizontal="left",  vertical="top", wrap_text=True)

HEADERS = [
    "TC ID",
    "Title",
    "Domain",
    "Generation Path",
    "Coverage Score",
    "Classification",
    "Best Match TC",
    "Scenario",
    "Preconditions",
    "Step No.",
    "Action",
    "Expected Result",
    "Final Expected Result",
]

COL_WIDTHS = [18, 40, 18, 16, 14, 18, 20, 45, 35, 8, 45, 45, 45]


def _write_header(ws) -> None:
    for col_idx, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font      = _HEADER_FONT
        cell.fill      = _HEADER_FILL
        cell.alignment = _CENTER
        cell.border    = _BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[1].height = 22


def _apply_row_style(ws, row: int, fill: PatternFill) -> None:
    for col in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill      = fill
        cell.border    = _BORDER
        cell.alignment = _LEFT


def _merge_tc_cols(ws, start_row: int, end_row: int, num_steps: int) -> None:
    if num_steps <= 1:
        return
    # Merge columns that don't change across steps (all except Step No./Action/Expected)
    for col in [1, 2, 3, 4, 5, 6, 7, 8, 9, 13]:
        ws.merge_cells(
            start_row=start_row, start_column=col,
            end_row=end_row,     end_column=col,
        )
        ws.cell(row=start_row, column=col).alignment = _LEFT


def build_excel(results: list[TestCaseResult]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Generated TestCases"
    ws.freeze_panes = "A2"

    _write_header(ws)

    current_row = 2
    for item in results:
        tc   = item.testcase
        cov  = item.coverage
        steps = tc.steps if tc.steps else []

        best_match_title = ""
        best = cov.best_match
        if best:
            best_match_title = best.payload.get("title", str(best.qdrant_point_id))

        preconditions_text = "\n".join(tc.preconditions)
        num_steps = max(len(steps), 1)
        start_row = current_row

        for step_idx, step in enumerate(steps or [None]):
            fill = _TC_FILL if step_idx % 2 == 0 else _STEP_FILL_ODD
            _apply_row_style(ws, current_row, fill)

            ws.cell(current_row, 1,  tc.testcase_id)
            ws.cell(current_row, 2,  tc.title)
            ws.cell(current_row, 3,  tc.domain)
            ws.cell(current_row, 4,  tc.generation_path)
            ws.cell(current_row, 5,  tc.coverage_score)
            ws.cell(current_row, 6,  tc.coverage_classification)
            ws.cell(current_row, 7,  best_match_title)
            ws.cell(current_row, 8,  item.scenario_text)
            ws.cell(current_row, 9,  preconditions_text)
            ws.cell(current_row, 13, tc.final_expected_result)

            if step is not None:
                ws.cell(current_row, 10, step.step_number)
                ws.cell(current_row, 11, step.action)
                ws.cell(current_row, 12, step.expected_result)

            ws.row_dimensions[current_row].height = 55
            current_row += 1

        _merge_tc_cols(ws, start_row, start_row + num_steps - 1, num_steps)

    # Auto-filter on header row
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}1"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
