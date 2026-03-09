import json


def export_report(result, path="report.json"):

    report = {
        "summary": result["final_report"]["summary"],
        "score": result["final_report"]["score"],
        "main_errors": result["final_report"]["main_errors"],
        "recommendations": result["final_report"]["recommendations"],
        "conclusion": result["final_report"]["conclusion"],
        "stages": result["structure_result"]["stages"],
        "usage": result["total_usage"]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Отчёт сохранён: {path}")


def export_text_report(result, path="report.txt"):

    final = result["final_report"]

    text = f"""
=== АНАЛИЗ ЗВОНКА ===

РЕЗЮМЕ
{final.get("summary","")}

ОЦЕНКА СКРИПТА
{final.get("score",0)}/100

ОШИБКИ
"""

    for err in final.get("main_errors", []):

        if isinstance(err, dict):
            text += f"- {err.get('type','')}: {err.get('explanation','')}\n"

        else:
            text += f"- {err}\n"

    text += "\nРЕКОМЕНДАЦИИ\n"

    for rec in final.get("recommendations", []):

        if isinstance(rec, dict):
            text += f"- {rec.get('recommendation','')}\n"

        else:
            text += f"- {rec}\n"

    text += f"""

ЗАКЛЮЧЕНИЕ
{final.get("conclusion","")}

TOKENS
{result.get("total_usage",{})}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Текстовый отчёт сохранён: {path}")