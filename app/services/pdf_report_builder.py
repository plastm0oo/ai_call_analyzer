from __future__ import annotations

import ast
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

class PDFReportBuilder:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.font_name = self._register_fonts()

        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "TitleRu",
            parent=styles["Title"],
            fontName=self.font_name,
            fontSize=18,
            leading=22,
            spaceAfter=12,
            textColor=colors.HexColor("#111827"),
        )
        self.section_style = ParagraphStyle(
            "SectionRu",
            parent=styles["Heading2"],
            fontName=self.font_name,
            fontSize=13,
            leading=16,
            spaceAfter=8,
            textColor=colors.HexColor("#1f2937"),
        )
        self.body_style = ParagraphStyle(
            "BodyRu",
            parent=styles["BodyText"],
            fontName=self.font_name,
            fontSize=10,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor("#111827"),
        )
        self.small_style = ParagraphStyle(
            "SmallRu",
            parent=self.body_style,
            fontName=self.font_name,
            fontSize=9,
            leading=11,
            spaceAfter=4,
        )

    def _register_fonts(self) -> None:
        app_dir = Path(__file__).resolve().parent.parent
        static_dir = app_dir / "static"
        
        candidates = [
            static_dir / "Roboto-Regular.ttf",
            static_dir / "Roboto-Regulat.ttf",  # на случай опечатки в имени файла
            static_dir / "DejaVuSans.ttf",
            static_dir / "Arial Unicode.ttf",
        ]

        font_path = next((p for p in candidates if p.exists()), None)
        if font_path is None:
            looked = "\n".join(str(p) for p in candidates)
            raise FileNotFoundError(
                "Не найден TTF-шрифт с кириллицей. Проверь app/static/.\n"
                f"Проверены пути:\n{looked}"
            )

        internal_name = "ReportFontRU"
        try:
            pdfmetrics.getFont(internal_name)
        except KeyError:
            pdfmetrics.registerFont(TTFont(internal_name, str(font_path)))

        return internal_name

    def build(self, report_data: dict[str, Any], filename: str, call_id: str | None = None) -> Path:
        pdf_path = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        story = []

        story.append(self._p("Коучинговый отчет по звонку", self.title_style))
        if call_id:
            story.append(self._p(f"Call ID: {call_id}", self.body_style))
        story.append(Spacer(1, 6))

        normalized = self._normalize_report(report_data)

        # 1. Краткий итог
        story.append(self._p("1. Краткий итог", self.section_style))
        story.append(self._p(f"Итоговый балл: {normalized['score']}", self.body_style))
        story.append(self._p(f"Краткое резюме: {normalized['summary']}", self.body_style))
        story.append(self._p(f"Вывод: {normalized['conclusion']}", self.body_style))
        if normalized["main_errors"]:
            story.append(self._p(
                "Основные проблемы: " + ", ".join(normalized["main_errors"]),
                self.body_style,
            ))
        story.append(Spacer(1, 8))

        # 2. Этапы
        story.append(self._p("2. Анализ этапов звонка", self.section_style))
        if normalized["dialog_stages"]:
            table_data = [
                [
                    self._p("Этап", self.small_style),
                    self._p("Найден", self.small_style),
                    self._p("Подтверждающие реплики", self.small_style),
                ]
            ]
            for item in normalized["dialog_stages"]:
                replicas = item.get("replicas", [])
                replicas_text = "<br/>".join(escape(str(r)) for r in replicas) if replicas else "—"
                table_data.append([
                    self._p(str(item.get("stage", "—")), self.small_style),
                    self._p("Да" if item.get("found") else "Нет", self.small_style),
                    Paragraph(replicas_text, self.small_style),
                ])

            table = Table(table_data, colWidths=[45 * mm, 22 * mm, 95 * mm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
        else:
            story.append(self._p("Этапы звонка не найдены.", self.body_style))

        if normalized["missing_stages"]:
            story.append(Spacer(1, 6))
            story.append(self._p(
                "Пропущенные этапы: " + ", ".join(normalized["missing_stages"]),
                self.body_style,
            ))
        if normalized["script_comment"]:
            story.append(self._p(
                "Комментарий: " + normalized["script_comment"],
                self.body_style,
            ))
        story.append(Spacer(1, 10))

        # 3. Ошибки
        story.append(self._p("3. Ошибки", self.section_style))
        if normalized["mistakes"]:
            for idx, mistake in enumerate(normalized["mistakes"], start=1):
                story.append(self._p(f"{idx}. Тип: {mistake.get('type', 'Ошибка')}", self.body_style))
                story.append(self._p(f"Цитата: {mistake.get('quote', '—')}", self.body_style))
                story.append(self._p(f"Пояснение: {mistake.get('description', '—')}", self.body_style))
                story.append(Spacer(1, 3))
        else:
            story.append(self._p("Ошибки не обнаружены.", self.body_style))
        story.append(Spacer(1, 8))

        # 4. Рекомендации
        story.append(self._p("4. Рекомендации", self.section_style))
        if normalized["recommendations"]:
            for idx, rec in enumerate(normalized["recommendations"], start=1):
                story.append(self._p(f"{idx}. {rec}", self.body_style))
        else:
            story.append(self._p("Рекомендации отсутствуют.", self.body_style))

        doc.build(story)
        return pdf_path

    def _normalize_report(self, report_data: dict[str, Any]) -> dict[str, Any]:
        # Поддержка двух форматов:
        # 1) старый: summary={}, meta={}, script_analysis={}, mistakes=[], dialog_stages=[]
        # 2) новый: summary='...', score=..., main_errors=[], recommendations=[{description, example}], conclusion='...'

        summary_block = report_data.get("summary")
        if isinstance(summary_block, dict):
            summary_text = str(summary_block.get("short_summary") or summary_block.get("summary") or "—")
            conclusion_text = str(summary_block.get("result") or report_data.get("conclusion") or "—")
        else:
            summary_text = str(summary_block or "—")
            conclusion_text = str(report_data.get("conclusion") or "—")

        script_analysis = report_data.get("script_analysis", {}) or {}
        meta = report_data.get("meta", {}) or {}

        score = (
            report_data.get("score")
            or meta.get("raw_score")
            or script_analysis.get("followed_score")
            or "—"
        )

        main_errors = report_data.get("main_errors") or meta.get("main_errors") or []
        dialog_stages = self._normalize_stages(report_data.get("dialog_stages") or report_data.get("stages") or [])
        mistakes = self._normalize_mistakes(report_data.get("mistakes") or report_data.get("errors") or [])
        recommendations = self._normalize_recommendations(report_data.get("recommendations") or [])
        missing_stages = report_data.get("missed_stages") or script_analysis.get("missing_stages") or []
        script_comment = report_data.get("comment") or script_analysis.get("comment") or ""

        return {
            "summary": summary_text,
            "conclusion": conclusion_text,
            "score": score,
            "main_errors": [str(x) for x in main_errors],
            "dialog_stages": dialog_stages,
            "mistakes": mistakes,
            "recommendations": recommendations,
            "missing_stages": [str(x) for x in missing_stages],
            "script_comment": str(script_comment),
        }

    def _normalize_stages(self, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in stages:
            result.append({
                "stage": item.get("stage", "—"),
                "found": bool(item.get("found", False)),
                "replicas": item.get("replicas") or item.get("quotes") or [],
            })
        return result

    def _normalize_mistakes(self, mistakes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in mistakes:
            result.append({
                "type": item.get("type", "Ошибка"),
                "quote": item.get("quote", "—"),
                "description": item.get("description") or item.get("explanation") or "—",
            })
        return result

    def _normalize_recommendations(self, recommendations: list[Any]) -> list[str]:
        result: list[str] = []
        for item in recommendations:
            if isinstance(item, str):
                result.append(item)
                continue

            if isinstance(item, dict):
                # новый формат
                description = item.get("description")
                example = item.get("example")
                suggestion = item.get("suggestion") or item.get("suggestedText")
                rtype = item.get("type")

                parts = []
                if rtype:
                    parts.append(str(rtype))
                if description:
                    parts.append(str(description))
                if suggestion:
                    parts.append(str(suggestion))
                if example:
                    parts.append(f"Пример: {example}")

                if parts:
                    result.append(". ".join(parts))
                    continue

                # на случай, если dict пришел как {text: "{...}"}
                text = item.get("text")
                if isinstance(text, str):
                    parsed_text = self._parse_stringified_dict(text)
                    if parsed_text:
                        result.append(parsed_text)
                        continue
                    result.append(text)
                    continue

            result.append(str(item))
        return result

    def _parse_stringified_dict(self, text: str) -> str | None:
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            return None

        if not isinstance(parsed, dict):
            return None

        parts = []
        if parsed.get("type"):
            parts.append(str(parsed["type"]))
        if parsed.get("description"):
            parts.append(str(parsed["description"]))
        if parsed.get("suggestion"):
            parts.append(str(parsed["suggestion"]))
        if parsed.get("suggestedText"):
            parts.append(str(parsed["suggestedText"]))
        if parsed.get("example"):
            parts.append(f"Пример: {parsed['example']}")

        return ". ".join(parts) if parts else str(parsed)

    def _p(self, text: Any, style: ParagraphStyle) -> Paragraph:
        safe_text = escape(str(text)).replace("\n", "<br/>")
        return Paragraph(safe_text, style)
