import json

def export_report(result, path="report.json"):
    final = result["final_report"]

    report = {
        "summary": final["summary"],
        "score": final["script_analysis"]["followed_score"],
        "main_errors": final["meta"]["main_errors"],
        "recommendations": final["recommendations"],
        "conclusion": final["summary"]["result"],
        "stages": final["dialog_stages"],
        "usage": result.get("usage", {}),
        "transcript": result.get("transcript", ""),
        "role_transcript": result.get("role_transcript", ""),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Отчёт сохранён: {path}")

def export_text_report(result, path="report.txt"):
    final = result["final_report"]
    summary = final.get("summary", {}) or {}
    script = final.get("script_analysis", {}) or {}
    meta = final.get("meta", {}) or {}

    short_summary = summary.get("short_summary", "")
    conclusion = summary.get("result", "")
    score = script.get("followed_score", 0)

    text = f"""
=== АНАЛИЗ ЗВОНКА ===

КРАТКОЕ РЕЗЮМЕ
{short_summary}

ИТОГ
{conclusion}

ОЦЕНКА СКРИПТА
{score}/100

ОСНОВНЫЕ ОШИБКИ
"""

    for err in meta.get("main_errors", []):
        text += f"- {err}\n"

    text += "\nРЕКОМЕНДАЦИИ\n"

    for rec in final.get("recommendations", []):
        if isinstance(rec, dict):
            text += f"- [{rec.get('category', 'general')}] {rec.get('text', '')}\n"
        else:
            text += f"- {rec}\n"

    text += f"""

TOKENS
{result.get("usage", {})}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Текстовый отчёт сохранён: {path}")