import json
import os


REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def save_report_to_file(call_id: str, report_data: dict) -> str:
    file_path = os.path.join(REPORT_DIR, f"{call_id}_report.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

    return file_path