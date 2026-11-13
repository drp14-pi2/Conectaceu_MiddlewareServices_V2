from io import BytesIO
from typing import Any
import base64

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


class XlsxRenderService:
    """Renders tabular dicts to XLSX"""

    @staticmethod
    def render_to_base64(
        rows: list[dict[str, Any]],
        sheet_name: str = "Sheet1",
        column_labels: dict[str, str] | None = None,
        column_order: list[str] | None = None,
    ) -> str:
        """Returns base64-encoded XLSX"""
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name[:31]  # Excel caps sheet names at 31 chars

        if not rows:
            ws.append(["Nenhum registro encontrado"])

            return XlsxRenderService._to_base64(wb)

        columns = column_order or list(rows[0].keys())
        labels = column_labels or {c: c for c in columns}

        # Header
        ws.append([labels.get(c, c) for c in columns])
        header_fill = PatternFill("solid", fgColor="DDDDDD")

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Data
        for row in rows:
            ws.append([row.get(c) for c in columns])

        # Column widths (approximate)
        for i, col in enumerate(columns, start=1):
            max_len = max(
                len(str(labels.get(col, col))),
                *(len(str(r.get(col, ""))) for r in rows),
            )
            ws.column_dimensions[get_column_letter(i)].width = min(max_len + 2, 60)

        ws.freeze_panes = "A2"  # Keep header visible

        return XlsxRenderService._to_base64(wb)

    @staticmethod
    def _to_base64(wb: Workbook) -> str:
        buffer = BytesIO()
        wb.save(buffer)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
