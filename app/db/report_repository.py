from __future__ import annotations

import ast
import json
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

class CoachingReportRepository:
    def save_report(
        self,
        db: Session,
        *,
        employee_id: int,
        call_id: str,
        report_data: dict[str, Any],
        raw_json_path: str | None = None,
        pdf_path: str | None = None,
    ) -> int:
        if not isinstance(report_data, dict):
            raise ValueError("report_data must be a dict")

        summary = report_data.get("summary") or {}
        script_analysis = report_data.get("script_analysis") or {}
        meta = report_data.get("meta") or {}

        raw_score = meta.get("raw_score", script_analysis.get("followed_score", 0))
        short_summary = summary.get("short_summary")
        result_text = summary.get("result")
        main_errors = meta.get("main_errors", []) or []
        missing_stages = script_analysis.get("missing_stages", []) or []
        comment = script_analysis.get("comment")

        try:
            report_id = db.execute(
                text(
                    """
                    INSERT INTO call_reports (
                        employee_id,
                        call_id,
                        raw_score,
                        short_summary,
                        result_text,
                        script_comment,
                        main_errors,
                        missing_stages,
                        full_report_json,
                        raw_json_path,
                        pdf_path
                    )
                    VALUES (
                        :employee_id,
                        :call_id,
                        :raw_score,
                        :short_summary,
                        :result_text,
                        :script_comment,
                        CAST(:main_errors AS jsonb),
                        CAST(:missing_stages AS jsonb),
                        CAST(:full_report_json AS jsonb),
                        :raw_json_path,
                        :pdf_path
                    )
                    ON CONFLICT (call_id)
                    DO UPDATE SET
                        employee_id = EXCLUDED.employee_id,
                        raw_score = EXCLUDED.raw_score,
                        short_summary = EXCLUDED.short_summary,
                        result_text = EXCLUDED.result_text,
                        script_comment = EXCLUDED.script_comment,
                        main_errors = EXCLUDED.main_errors,
                        missing_stages = EXCLUDED.missing_stages,
                        full_report_json = EXCLUDED.full_report_json,
                        raw_json_path = EXCLUDED.raw_json_path,
                        pdf_path = EXCLUDED.pdf_path,
                        updated_at = NOW()
                    RETURNING id
                    """
                ),
                {
                    "employee_id": employee_id,
                    "call_id": call_id,
                    "raw_score": raw_score,
                    "short_summary": short_summary,
                    "result_text": result_text,
                    "script_comment": comment,
                    "main_errors": self._to_json(main_errors),
                    "missing_stages": self._to_json(missing_stages),
                    "full_report_json": self._to_json(report_data),
                    "raw_json_path": raw_json_path,
                    "pdf_path": pdf_path,
                },
            ).scalar_one()

            self._delete_children(db, int(report_id))

            self._insert_dialog_stages(db, int(report_id), report_data.get("dialog_stages", []))
            self._insert_mistakes(db, int(report_id), report_data.get("mistakes", []))
            self._insert_recommendations(db, int(report_id), report_data.get("recommendations", []))

            db.commit()
            return int(report_id)

        except Exception:
            db.rollback()
            raise

    def _delete_children(self, db: Session, report_id: int) -> None:
        db.execute(text("DELETE FROM call_dialog_stages WHERE report_id = :report_id"), {"report_id": report_id})
        db.execute(text("DELETE FROM call_mistakes WHERE report_id = :report_id"), {"report_id": report_id})
        db.execute(text("DELETE FROM call_recommendations WHERE report_id = :report_id"), {"report_id": report_id})

    def _insert_dialog_stages(
        self,
        db: Session,
        report_id: int,
        dialog_stages: list[dict[str, Any]],
    ) -> None:
        for item in dialog_stages or []:
            db.execute(
                text(
                    """
                    INSERT INTO call_dialog_stages (
                        report_id,
                        stage_name,
                        found,
                        replicas
                    )
                    VALUES (
                        :report_id,
                        :stage_name,
                        :found,
                        CAST(:replicas AS jsonb)
                    )
                    """
                ),
                {
                    "report_id": report_id,
                    "stage_name": item.get("stage"),
                    "found": bool(item.get("found", False)),
                    "replicas": self._to_json(item.get("replicas", [])),
                },
            )

    def _insert_mistakes(self, db: Session, report_id: int, mistakes: list[dict[str, Any]]) -> None:
        for item in mistakes or []:
            db.execute(
                text(
                    """
                    INSERT INTO call_mistakes (
                        report_id,
                        mistake_type,
                        quote,
                        description
                    )
                    VALUES (
                        :report_id,
                        :mistake_type,
                        :quote,
                        :description
                    )
                    """
                ),
                {
                    "report_id": report_id,
                    "mistake_type": item.get("type"),
                    "quote": item.get("quote"),
                    "description": item.get("description"),
                },
            )

    def _insert_recommendations(
        self,
        db: Session,
        report_id: int,
        recommendations: list[dict[str, Any]],
    ) -> None:
        for item in recommendations or []:
            normalized = self._normalize_recommendation(item)
            db.execute(
                text(
                    """
                    INSERT INTO call_recommendations (
                        report_id,
                        recommendation_type,
                        recommendation_subtype,
                        suggestion,
                        raw_text
                    )
                    VALUES (
                        :report_id,
                        :recommendation_type,
                        :recommendation_subtype,
                        :suggestion,
                        :raw_text
                    )
                    """
                ),
                {
                    "report_id": report_id,
                    "recommendation_type": normalized.get("type"),
                    "recommendation_subtype": normalized.get("subtype"),
                    "suggestion": normalized.get("suggestion"),
                    "raw_text": item.get("text"),
                },
            )

    @staticmethod
    def _normalize_recommendation(item: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "type": item.get("type"),
            "subtype": item.get("subtype"),
            "suggestion": item.get("suggestion"),
        }

        raw_text = item.get("text")

        if isinstance(raw_text, str) and raw_text.strip().startswith("{"):
            parsed = None

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(raw_text)
                except (ValueError, SyntaxError):
                    parsed = None

            if isinstance(parsed, dict):
                normalized["type"] = normalized["type"] or parsed.get("type")
                normalized["subtype"] = normalized["subtype"] or parsed.get("subtype")
                normalized["suggestion"] = normalized["suggestion"] or parsed.get("suggestion")

        elif isinstance(raw_text, str) and not normalized.get("suggestion"):
            normalized["suggestion"] = raw_text

        return normalized

    @staticmethod
    def _to_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)