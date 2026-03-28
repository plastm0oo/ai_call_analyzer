import json
import os
from typing import Any, Dict

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def build_report_payload(call_id: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    final = analysis_result.get("final_report", {}) or {}

    return {
        "call_id": call_id,
        "summary": final.get("summary", {}),
        "dialog_stages": final.get("dialog_stages", []),
        "script_analysis": final.get("script_analysis", {}),
        "mistakes": final.get("mistakes", []),
        "recommendations": final.get("recommendations", []),
        "meta": final.get("meta", {}),
        "usage": analysis_result.get("usage", {}),
        "transcript": analysis_result.get("transcript", ""),
        "role_transcript": analysis_result.get("role_transcript", ""),
    }

def save_report_to_file(call_id: str, analysis_result: dict) -> str:
    file_path = os.path.join(REPORT_DIR, f"{call_id}.json")
    payload = build_report_payload(call_id, analysis_result)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    return file_path