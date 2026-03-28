from __future__ import annotations

import json
from pathlib import Path
from app.services.pdf_report_builder import PDFReportBuilder

class CoachingReportService:
    def __init__(self, reports_dir: str = "reports") -> None:
        self.reports_dir = Path(reports_dir)
        self.pdf_dir = self.reports_dir / "pdf"

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_builder = PDFReportBuilder(output_dir=self.pdf_dir)

    def get_or_create_pdf(self, call_id: str) -> str:
        pdf_path = self.pdf_dir / f"{call_id}.pdf"
        if pdf_path.exists():
            return str(pdf_path)

        json_path = self._find_report_json(call_id)
        if not json_path:
            raise FileNotFoundError(f"JSON report for call_id={call_id} not found")

        with json_path.open("r", encoding="utf-8") as f:
            report_data = json.load(f)

        if not isinstance(report_data, dict):
            raise ValueError(f"Invalid report JSON for call_id={call_id}")
        
        generated_pdf_path = self.pdf_builder.build(
            report_data=report_data,
            filename=f"{call_id}.pdf",
            call_id=call_id,
        )
        return str(generated_pdf_path)

    def _find_report_json(self, call_id: str) -> Path | None:
        exact_path = self.reports_dir / f"{call_id}.json"
        if exact_path.exists():
            return exact_path

        matches = list(self.reports_dir.glob(f"{call_id}*.json"))
        if matches:
            return matches[0]

        return None