from pathlib import Path
from typing import Any, Dict, List

from app.llm_module.agents import GigaChatAgentPipeline
from app.llm_module.rag import retrieve_knowledge

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "llm_module" / "knowledge"

def _read_text_file(filename: str) -> str:
    path = KNOWLEDGE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {path}")
    return path.read_text(encoding="utf-8").strip()

def load_knowledge_fallback() -> Dict[str, str]:
    return {
        "stages_text": _read_text_file("stages.txt"),
        "script_text": _read_text_file("script.txt"),
        "criteria_text": _read_text_file("criteria.txt"),
        "coach_tips_text": _read_text_file("coach_tips.txt"),
    }

def load_knowledge_for_transcript(transcript: str) -> Dict[str, str]:
    knowledge_texts = {}
    knowledge_types = ["stages", "script", "criteria", "coach_tips"]
    for ktype in knowledge_types:
        chunks = retrieve_knowledge(transcript, top_k=3, filter_type=ktype)
        if chunks:
            knowledge_texts[f"{ktype}_text"] = "\n\n".join(chunks)
        else:
            file_path = KNOWLEDGE_DIR / f"{ktype}.txt"
            knowledge_texts[f"{ktype}_text"] = file_path.read_text(encoding="utf-8").strip()
    return knowledge_texts

def _normalize_dialog_stages(structure_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = []
    for stage_item in structure_result.get("stages", []):
        if not isinstance(stage_item, dict):
            continue
        stage_name = str(stage_item.get("stage", "")).strip()
        quotes = stage_item.get("quotes", [])
        if not isinstance(quotes, list):
            quotes = [str(quotes)] if quotes else []
        replicas = [str(q).strip() for q in quotes if str(q).strip()]
        normalized.append({"stage": stage_name, "replicas": replicas})
    return normalized

def _normalize_script_analysis(script_check_result: Dict[str, Any]) -> Dict[str, Any]:
    score = script_check_result.get("score", 0)
    try:
        score = int(score)
    except Exception:
        score = 0
    missing_stages = script_check_result.get("missed_stages", [])
    if not isinstance(missing_stages, list):
        missing_stages = [str(missing_stages)] if missing_stages else []
    violations = script_check_result.get("violations", [])
    if not isinstance(violations, list):
        violations = [str(violations)] if violations else []
    return {
        "followed_score": max(0, min(100, score)),
        "missing_stages": [str(x).strip() for x in missing_stages if str(x).strip()],
        "violations": [str(x).strip() for x in violations if str(x).strip()],
        "comment": str(script_check_result.get("comment", "")).strip()
    }

def _normalize_mistakes(errors_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = []
    for err in errors_result.get("errors", []):
        if not isinstance(err, dict):
            continue
        err_type = str(err.get("type", "")).strip()
        quote = str(err.get("quote", "")).strip()
        explanation = str(err.get("explanation", "")).strip()
        if quote and explanation:
            description = f'Цитата: "{quote}". Пояснение: {explanation}'
        elif explanation:
            description = explanation
        elif quote:
            description = f'Цитата: "{quote}"'
        else:
            description = ""
        normalized.append({"type": err_type, "description": description})
    return normalized

def _normalize_recommendations(coaching_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = []
    for rec in coaching_result.get("recommendations", []):
        rec_text = str(rec).strip()
        if not rec_text:
            continue
        normalized.append({
            "problem": "Выявленные ошибки в звонке",
            "reason": "LLM определила зоны роста по структуре звонка и репликам менеджера",
            "recommendation": rec_text
        })
    return normalized

def _normalize_summary(final_report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "short_summary": str(final_report.get("summary", "")).strip(),
        "result": str(final_report.get("conclusion", "")).strip()
    }

def normalize_llm_result(
    call_id: str,
    transcript: str,
    raw_result: Dict[str, Any]
) -> Dict[str, Any]:
    structure_result = raw_result.get("structure_result", {})
    script_check_result = raw_result.get("script_check_result", {})
    errors_result = raw_result.get("errors_result", {})
    coaching_result = raw_result.get("coaching_result", {})
    final_report = raw_result.get("final_report", {})
    total_usage = raw_result.get("total_usage", {})

    dialog_structure = _normalize_dialog_stages(structure_result)
    script_analysis = _normalize_script_analysis(script_check_result)
    mistakes = _normalize_mistakes(errors_result)
    coaching_recommendations = _normalize_recommendations(coaching_result)
    summary = _normalize_summary(final_report)

    normalized_final_report = {
        "summary": summary,
        "dialog_stages": dialog_structure,
        "script_analysis": script_analysis,
        "mistakes": mistakes,
        "recommendations": coaching_recommendations
    }

    return {
        "call_id": call_id,
        "transcript": transcript,
        "dialog_structure": dialog_structure,
        "script_analysis": script_analysis,
        "mistakes": mistakes,
        "coaching_recommendations": coaching_recommendations,
        "final_report": normalized_final_report,
        "llm_raw_result": raw_result,
        "usage": total_usage
    }

def run_llm_analysis(call_id: str, transcript: str, debug: bool = True) -> Dict[str, Any]:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")
    knowledge = load_knowledge_for_transcript(transcript)
    pipeline = GigaChatAgentPipeline(debug=debug)
    raw_result = pipeline.run_pipeline(
        transcript=transcript,
        stages_text=knowledge["stages_text"],
        script_text=knowledge["script_text"],
        criteria_text=knowledge["criteria_text"],
        coach_tips_text=knowledge["coach_tips_text"]
    )
    return normalize_llm_result(
        call_id=call_id,
        transcript=transcript,
        raw_result=raw_result
    )