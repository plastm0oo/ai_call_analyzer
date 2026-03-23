from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


class PDFReportBuilder:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(self, report_data: dict[str, Any], output_filename: str) -> Path:
        output_path = self.output_dir / output_filename

        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="BodySmall",
                parent=styles["BodyText"],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
        )

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        story = []

        summary = report_data.get("summary", {})
        script_analysis = report_data.get("script_analysis", {})
        meta = report_data.get("meta", {})

        raw_score = meta.get("raw_score", script_analysis.get("followed_score", 0))
        status_text = self._score_to_status(raw_score)

        story.append(Paragraph("Коучинговый отчет по звонку", styles["Title"]))
        story.append(Spacer(1, 6))

        header_data = [
            ["Итоговый балл", str(raw_score)],
            ["Статус", status_text],
            ["Краткий вывод", summary.get("result", "—")],
        ]
        story.append(self._styled_table(header_data, col_widths=[45 * mm, 115 * mm]))
        story.append(Spacer(1, 10))

        story.append(Paragraph("1. Краткое резюме", styles["Heading2"]))
        story.append(Paragraph(summary.get("short_summary", "—"), styles["BodySmall"]))
        story.append(Paragraph(summary.get("result", "—"), styles["BodySmall"]))
        story.append(Spacer(1, 6))

        main_errors = meta.get("main_errors", []) or []
        if main_errors:
            story.append(Paragraph("Главные проблемы:", styles["Heading3"]))
            for item in main_errors:
                story.append(Paragraph(f"• {item}", styles["BodySmall"]))
            story.append(Spacer(1, 6))

        story.append(Paragraph("2. Анализ соблюдения скрипта", styles["Heading2"]))
        story.append(Paragraph(script_analysis.get("comment", "—"), styles["BodySmall"]))
        missing_stages = script_analysis.get("missing_stages", []) or []
        if missing_stages:
            story.append(Paragraph("Пропущенные этапы:", styles["Heading3"]))
            for stage in missing_stages:
                story.append(Paragraph(f"• {stage}", styles["BodySmall"]))
            story.append(Spacer(1, 6))

        dialog_stages = report_data.get("dialog_stages", []) or []
        if dialog_stages:
            story.append(Paragraph("Найденные этапы в звонке", styles["Heading3"]))
            stage_rows = [["Этап", "Найден", "Подтверждающие реплики"]]
            for item in dialog_stages:
                replicas = item.get("replicas", []) or []
                replicas_text = "<br/>".join(self._escape(r) for r in replicas) if replicas else "—"
                stage_rows.append(
                    [
                        self._escape(item.get("stage", "—")),
                        "Да" if item.get("found") else "Нет",
                        replicas_text,
                    ]
                )
            story.append(self._styled_table(stage_rows, header=True, col_widths=[40 * mm, 20 * mm, 110 * mm]))
            story.append(Spacer(1, 8))

        mistakes = report_data.get("mistakes", []) or []
        story.append(Paragraph("3. Ошибки и точки роста", styles["Heading2"]))
        if mistakes:
            mistake_rows = [["Тип", "Цитата", "Пояснение"]]
            for item in mistakes:
                mistake_rows.append(
                    [
                        self._escape(item.get("type", "—")),
                        self._escape(item.get("quote", "—")),
                        self._escape(item.get("description", "—")),
                    ]
                )
            story.append(self._styled_table(mistake_rows, header=True, col_widths=[35 * mm, 45 * mm, 90 * mm]))
        else:
            story.append(Paragraph("Критичных ошибок не обнаружено.", styles["BodySmall"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("4. Рекомендации для коучинга", styles["Heading2"]))
        recommendations = report_data.get("recommendations", []) or []
        normalized_recommendations = [self._normalize_recommendation(rec) for rec in recommendations]
        if normalized_recommendations:
            for idx, rec in enumerate(normalized_recommendations, start=1):
                title_parts = [rec.get("type") or "Рекомендация"]
                if rec.get("subtype"):
                    title_parts.append(f"({rec['subtype']})")
                story.append(Paragraph(f"{idx}. {' '.join(title_parts)}", styles["Heading3"]))
                story.append(Paragraph(rec.get("suggestion") or rec.get("text") or "—", styles["BodySmall"]))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("Рекомендации отсутствуют.", styles["BodySmall"]))

        coach_summary = self._build_coach_summary(report_data)
        story.append(Spacer(1, 8))
        story.append(Paragraph("5. Вывод для руководителя", styles["Heading2"]))
        story.append(Paragraph(coach_summary, styles["BodySmall"]))

        doc.build(story)
        return output_path

    @staticmethod
    def _escape(value: Any) -> str:
        text = str(value) if value is not None else "—"
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _score_to_status(score: int | float) -> str:
        if score >= 80:
            return "Сильный звонок"
        if score >= 60:
            return "Хороший базовый уровень"
        if score >= 40:
            return "Нужен точечный коучинг"
        return "Нужна системная проработка"

    def _styled_table(self, data: list[list[Any]], header: bool = False, col_widths: list[float] | None = None) -> Table:
        prepared = []
        for row_idx, row in enumerate(data):
            prepared_row = []
            for cell in row:
                style_name = "Heading4" if header and row_idx == 0 else "BodySmall"
                prepared_row.append(Paragraph(str(cell), getSampleStyleSheet()[style_name] if style_name != "BodySmall" else ParagraphStyle(name='tmp', parent=getSampleStyleSheet()['BodyText'], fontSize=9, leading=12)))
            prepared.append(prepared_row)

        table = Table(prepared, colWidths=col_widths, repeatRows=1 if header else 0)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFCFCF")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        if header:
            style.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EEF7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        table.setStyle(TableStyle(style))
        return table

    def _normalize_recommendation(self, rec: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "type": rec.get("type"),
            "subtype": rec.get("subtype"),
            "suggestion": rec.get("suggestion"),
            "text": rec.get("text"),
        }

        raw_text = rec.get("text")
        if isinstance(raw_text, str) and raw_text.strip().startswith("{"):
            try:
                parsed = ast.literal_eval(raw_text)
                if isinstance(parsed, dict):
                    normalized["subtype"] = normalized["subtype"] or parsed.get("type")
                    normalized["suggestion"] = normalized["suggestion"] or parsed.get("suggestion")
            except (ValueError, SyntaxError):
                pass

        return normalized

    def _build_coach_summary(self, report_data: dict[str, Any]) -> str:
        meta = report_data.get("meta", {})
        script_analysis = report_data.get("script_analysis", {})
        errors = meta.get("main_errors", []) or []
        missing = script_analysis.get("missing_stages", []) or []
        score = meta.get("raw_score", script_analysis.get("followed_score", 0))

        errors_text = ", ".join(errors[:3]) if errors else "явных системных ошибок не выявлено"
        missing_text = ", ".join(missing[:3]) if missing else "ключевые этапы не пропущены"

        return (
            f"Итоговый балл сотрудника: {score}. Основные проблемные зоны: {errors_text}. "
            f"В ближайшем коучинге стоит сфокусироваться на следующих этапах: {missing_text}. "
            f"Рекомендуется разобрать звонок по этапам, отработать формулировки и закрепить новые речевые паттерны на практике."
        )
