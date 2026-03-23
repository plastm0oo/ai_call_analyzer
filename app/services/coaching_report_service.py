from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.report_repository import CoachingReportRepository
from app.services.pdf_report_builder import PDFReportBuilder


@dataclass
class GeneratedReportArtifacts:
    call_id: str
    raw_json_path: str
    pdf_path: str
    db_report_id: int | None = None


class CoachingReportService:
    def __init__(self, repository: CoachingReportRepository | None = None) -> None:
        self.repository = repository or CoachingReportRepository()

        app_dir = Path(__file__).resolve().parent.parent
        self.reports_dir = app_dir / "reports"
        self.pdf_dir = self.reports_dir / "pdf"
        self.db_dir = app_dir / "db"

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_builder = PDFReportBuilder(self.pdf_dir)

    def process_report(
        self,
        *,
        db: Session,
        employee_id: int,
        call_id: str,
        report_data: dict[str, Any],
    ) -> GeneratedReportArtifacts:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{call_id}_{timestamp}"

        raw_json_path = self._save_raw_json(report_data, f"{base_filename}.json")
        pdf_path = self.pdf_builder.build(report_data, f"{base_filename}.pdf")

        db_report_id = self.repository.save_report(
            db,
            employee_id=employee_id,
            call_id=call_id,
            report_data=report_data,
            raw_json_path=str(raw_json_path),
            pdf_path=str(pdf_path),
        )

        return GeneratedReportArtifacts(
            call_id=call_id,
            raw_json_path=str(raw_json_path),
            pdf_path=str(pdf_path),
            db_report_id=db_report_id,
        )

    def process_report_from_file(
        self,
        *,
        db: Session,
        employee_id: int,
        call_id: str,
        source_json_path: str | Path,
    ) -> GeneratedReportArtifacts:
        source_path = Path(source_json_path)
        with source_path.open("r", encoding="utf-8") as f:
            report_data = json.load(f)

        return self.process_report(
            db=db,
            employee_id=employee_id,
            call_id=call_id,
            report_data=report_data,
        )

    def _save_raw_json(self, report_data: dict[str, Any], filename: str) -> Path:
        target_path = self.reports_dir / filename
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
        return target_path
