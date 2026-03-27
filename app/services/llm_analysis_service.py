import ast
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
    
    knowledge_sources = {}
    
    for ktype in knowledge_types:
        chunks, metadata = retrieve_knowledge(transcript, top_k=3, filter_type=ktype)
        if chunks:
            knowledge_texts[f"{ktype}_text"] = "\n\n".join(chunks)
            knowledge_sources[ktype] = {
                "source": "rag",
                "chunks_count": len(chunks),
                "filtered": metadata["filtered_count"],
                "found": metadata["found_count"],
                "used_fallback": metadata["used_fallback"]
            }
        else:
            file_path = KNOWLEDGE_DIR / f"{ktype}.txt"
            knowledge_texts[f"{ktype}_text"] = file_path.read_text(encoding="utf-8").strip()
            knowledge_sources[ktype] = {
                "source": "full_file",
                "file": f"{ktype}.txt"
            }
        print(f"KNOWLEDGE [{ktype}]: {knowledge_sources[ktype]}")
    
    return knowledge_texts

def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}

def _extract_role_transcript(raw_result: Dict[str, Any], fallback_transcript: str) -> str:
    """
    Пытаемся достать транскрипт с ролями из известных мест.
    Если конкретный агент пишет в другой ключ, его надо добавить сюда один раз.
    """
    candidates = [
        raw_result.get("role_transcript"),
        raw_result.get("dialogue_transcript"),
        raw_result.get("speaker_transcript"),
        raw_result.get("formatted_transcript"),
    ]

    classification_result = _as_dict(raw_result.get("classification_result"))
    candidates.extend([
        classification_result.get("role_transcript"),
        classification_result.get("dialogue_transcript"),
        classification_result.get("speaker_transcript"),
        classification_result.get("formatted_transcript"),
        classification_result.get("transcript"),
    ])
    
    for value in candidates:
        if isinstance(value, str) and value.strip():
            text = value.strip()
            if "Менеджер:" in text or "Клиент:" in text:
                return text

    return fallback_transcript.strip()

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

    if not isinstance(raw_result, dict):
        raw_result = {}

    # llm_analysis_service.py
    print("RAW RESULT KEYS:", list(raw_result.keys()))
    print("TOP LEVEL RECOMMENDATIONS:", raw_result.get("recommendations"))
    print("TOP LEVEL TRAINING FOCUS:", raw_result.get("training_focus"))
    print("COACHING RESULT:", raw_result.get("coaching_result"))
    print("ROLE TRANSCRIPT EXISTS:", bool(_extract_role_transcript(raw_result, transcript)))

    return {
        "call_id": call_id,
        "transcript": transcript,
        "role_transcript": _extract_role_transcript(raw_result, transcript),
        "classification_result": _as_dict(raw_result.get("classification_result")),
        "structure_result": _as_dict(raw_result.get("structure_result")),
        "script_check_result": _as_dict(raw_result.get("script_check_result")),
        # Поддерживаем оба имени ключа, чтобы не зависеть от расхождения naming'а
        "manager_errors_result": _as_dict(
            raw_result.get("manager_errors_result") or raw_result.get("errors_result")
        ),
        "coaching_result": _as_dict(raw_result.get("coaching_result")),
        "final_report": _as_dict(raw_result.get("final_report")),
        "usage": _as_dict(raw_result.get("total_usage") or raw_result.get("usage")),
        "llm_raw_result": raw_result,
    }