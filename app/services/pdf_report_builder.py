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
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


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
        self.meta_style = ParagraphStyle(
            "MetaRu",
            parent=self.body_style,
            fontName=self.font_name,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4B5563"),
            spaceAfter=3,
        )

    def _register_fonts(self) -> str:
        app_dir = Path(__file__).resolve().parent.parent
        static_dir = app_dir / "static"

        candidates = [
            static_dir / "Roboto-Regular.ttf",
            static_dir / "Roboto-Regulat.ttf",
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

        normalized = self._normalize_report(report_data)

        story = []
        story.append(self._p("Коучинговый отчет по звонку", self.title_style))
        if call_id:
            story.append(self._p(f"Call ID: {call_id}", self.meta_style))
        story.append(Spacer(1, 6))

        # 1. Краткий итог
        story.append(self._p("1. Краткий итог", self.section_style))
        story.append(self._p(f"Итоговый балл: {normalized['score']}/100", self.body_style))
        story.append(self._p(f"Краткое резюме: {normalized['summary']}", self.body_style))
        story.append(self._p(f"Результат звонка: {normalized['conclusion']}", self.body_style))
        if normalized["main_errors"]:
            story.append(self._p(
                "Основные проблемы: " + "; ".join(normalized["main_errors"]),
                self.body_style,
            ))
        if normalized["training_focus"]:
            story.append(self._p(
                "Фокус развития: " + "; ".join(normalized["training_focus"]),
                self.body_style,
            ))
        story.append(Spacer(1, 8))

        # 2. Анализ скрипта
        story.append(self._p("2. Следование скрипту", self.section_style))
        if normalized["missing_stages"]:
            story.append(self._p(
                "Пропущенные этапы: " + ", ".join(normalized["missing_stages"]),
                self.body_style,
            ))
        else:
            story.append(self._p("Пропущенные этапы не обнаружены.", self.body_style))

        if normalized["violations"]:
            story.append(self._p(
                "Нарушения: " + "; ".join(normalized["violations"]),
                self.body_style,
            ))
        else:
            story.append(self._p("Выраженных нарушений не обнаружено.", self.body_style))

        if normalized["script_comment"]:
            story.append(self._p(
                "Комментарий по скрипту: " + normalized["script_comment"],
                self.body_style,
            ))
        story.append(Spacer(1, 8))

        # 3. Этапы звонка
        story.append(self._p("3. Этапы диалога", self.section_style))
        if normalized["dialog_stages"]:
            table_data = [[
                self._p("Этап", self.small_style),
                self._p("Найден", self.small_style),
                self._p("Подтверждающие реплики", self.small_style),
            ]]
            for item in normalized["dialog_stages"]:
                replicas = item.get("replicas", [])
                replicas_text = "<br/>".join(escape(str(r)) for r in replicas) if replicas else "—"
                table_data.append([
                    self._p(str(item.get("stage", "—")), self.small_style),
                    self._p("Да" if item.get("found") else "Нет", self.small_style),
                    Paragraph(replicas_text, self.small_style),
                ])

            table = Table(table_data, colWidths=[42 * mm, 20 * mm, 102 * mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
        else:
            story.append(self._p("Этапы звонка не найдены.", self.body_style))
        story.append(Spacer(1, 10))

        # 4. Ошибки
        story.append(self._p("4. Ошибки менеджера", self.section_style))
        if normalized["mistakes"]:
            for idx, mistake in enumerate(normalized["mistakes"], start=1):
                block = [
                    self._p(f"{idx}. Тип: {mistake.get('type', 'Ошибка')}", self.body_style),
                    self._p(f"Цитата: {mistake.get('quote', '—')}", self.body_style),
                    self._p(f"Пояснение: {mistake.get('description', '—')}", self.body_style),
                    Spacer(1, 3),
                ]
                story.append(KeepTogether(block))
        else:
            story.append(self._p("Ошибки не обнаружены.", self.body_style))
        story.append(Spacer(1, 8))

        # 5. Рекомендации
        story.append(self._p("5. Рекомендации", self.section_style))
        if normalized["recommendations"]:
            for idx, rec in enumerate(normalized["recommendations"], start=1):
                block = [
                    self._p(f"{idx}. Зона роста: {rec.get('zone_of_growth', '—')}", self.body_style),
                    self._p(f"Почему это важно: {rec.get('why_important', '—')}", self.body_style),
                    self._p(f"Что улучшать: {rec.get('what_to_improve', rec.get('text', '—'))}", self.body_style),
                    Spacer(1, 4),
                ]
                story.append(KeepTogether(block))
        else:
            story.append(self._p("Рекомендации отсутствуют.", self.body_style))
        story.append(Spacer(1, 8))

        # 6. Транскрипт
        story.append(self._p("6. Транскрипт", self.section_style))
        transcript_text = normalized["role_transcript"] or normalized["transcript"]
        story.append(self._p(transcript_text or "Транскрипт отсутствует.", self.body_style))

        doc.build(story)
        return pdf_path

    def _normalize_report(self, report_data: dict[str, Any]) -> dict[str, Any]:
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
            or 0
        )

        return {
            "summary": summary_text,
            "conclusion": conclusion_text,
            "score": score,
            "main_errors": [str(x) for x in (report_data.get("main_errors") or meta.get("main_errors") or [])],
            "training_focus": [str(x) for x in (meta.get("training_focus") or report_data.get("training_focus") or [])],
            "dialog_stages": self._normalize_stages(report_data.get("dialog_stages") or report_data.get("stages") or []),
            "mistakes": self._normalize_mistakes(report_data.get("mistakes") or report_data.get("errors") or []),
            "recommendations": self._normalize_recommendations(report_data.get("recommendations") or []),
            "missing_stages": self._normalize_missing_stages(
                report_data.get("missed_stages") or script_analysis.get("missing_stages") or []
            ),
            "violations": [str(x) for x in (report_data.get("violations") or script_analysis.get("violations") or [])],
            "script_comment": str(report_data.get("comment") or script_analysis.get("comment") or ""),
            "transcript": str(report_data.get("transcript") or ""),
            "role_transcript": str(report_data.get("role_transcript") or ""),
        }

    def _normalize_stages(self, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for item in stages:
            result.append({
                "stage": item.get("stage", "—"),
                "found": bool(item.get("found", False)),
                "replicas": item.get("replicas") or item.get("quotes") or [],
            })
        return result

    def _normalize_mistakes(self, mistakes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for item in mistakes:
            result.append({
                "type": item.get("type", "Ошибка"),
                "quote": item.get("quote", "—"),
                "description": item.get("description") or item.get("explanation") or "—",
            })
        return result

    def _normalize_recommendations(self, recommendations: list[Any]) -> list[dict[str, str]]:
        result = []
        for item in recommendations:
            parsed = item

            if isinstance(item, str):
                parsed = self._parse_stringified_dict(item) or {"text": item}

            if not isinstance(parsed, dict):
                continue

            text = str(parsed.get("text") or parsed.get("recommendation") or "").strip()
            result.append({
                "zone_of_growth": str(parsed.get("zone_of_growth") or parsed.get("problem") or parsed.get("category") or parsed.get("type") or "—"),
                "why_important": str(parsed.get("why_important") or parsed.get("reason") or "—"),
                "what_to_improve": str(parsed.get("what_to_improve") or parsed.get("recommendation") or text or "—"),
                "text": text or str(parsed),
            })
        return result

    def _normalize_missing_stages(self, value: list[Any]) -> list[str]:
        result = []
        for item in value:
            parsed = item
            if isinstance(item, str):
                try:
                    literal = ast.literal_eval(item)
                    if isinstance(literal, dict):
                        parsed = literal
                except Exception:
                    pass

            if isinstance(parsed, dict):
                stage_name = parsed.get("stage")
                if stage_name:
                    result.append(str(stage_name))
            else:
                result.append(str(parsed))

        return result

    def _parse_stringified_dict(self, text: str) -> dict[str, Any] | None:
        try:
            parsed = ast.literal_eval(text)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _p(self, text: Any, style: ParagraphStyle) -> Paragraph:
        safe_text = escape(str(text)).replace("\n", "<br/>")
        return Paragraph(safe_text, style)