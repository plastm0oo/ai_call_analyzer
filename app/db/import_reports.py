from __future__ import annotations

import json
from pathlib import Path

from app.db.report_repository import CoachingReportRepository
from app.db.session import SessionLocal

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def import_reports() -> None:
    repo = CoachingReportRepository()

    json_files = sorted(REPORTS_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON reports found in: {REPORTS_DIR}")
        return

    with SessionLocal() as db:
        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            call_id = report_data.get("call_id") or json_file.stem

            # Подстрой под свою структуру JSON
            employee_id = report_data.get("employee_id") or 1

            pdf_path = report_data.get("pdf_path")
            if not pdf_path:
                possible_pdf = json_file.with_suffix(".pdf")
                if possible_pdf.exists():
                    pdf_path = str(possible_pdf)

            report_id = repo.save_report(
                db,
                employee_id=employee_id,
                call_id=call_id,
                report_data=report_data,
                raw_json_path=str(json_file),
                pdf_path=pdf_path,
            )

            print(f"Imported {json_file.name} -> report_id={report_id}")


if __name__ == "__main__":
    import_reports()