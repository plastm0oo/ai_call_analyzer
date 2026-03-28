import ast

from app.services.llm_analysis_service import run_llm_analysis

USE_LLM_PIPELINE = True

def run_stub_pipeline(call_id: str, transcript: str) -> dict:
    data = {
        "call_id": call_id,
        "transcript": transcript,
        "classification_result": {},
        "structure_result": {},
        "script_check_result": {},
        "manager_errors_result": {},
        "coaching_result": {},
        "final_report": {},
        "usage": {},
    }

    return data

def _as_dict(value):
    return value if isinstance(value, dict) else {}

def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

PLACEHOLDER_TEXTS = {"—", "–", "-"}

def _clean_str(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in PLACEHOLDER_TEXTS:
        return ""
    return text

def _first_nonempty_str(*values) -> str:
    for value in values:
        if value is None or isinstance(value, (dict, list, tuple, set)):
            continue
        text = _clean_str(value)
        if text:
            return text
    return ""

def _has_content(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(_clean_str(value))
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True

def _pick_score(*values) -> int:
    for v in values:
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            return max(0, min(100, int(v)))
        if isinstance(v, str) and v.strip().isdigit():
            return max(0, min(100, int(v.strip())))
    return 0

CATEGORY_ALIASES = {
    "greeting": "greeting",
    "приветствие": "greeting",

    "needs_assessment": "needs_discovery",
    "needs_discovery": "needs_discovery",
    "needs_identification": "needs_discovery",
    "выявление потребности": "needs_discovery",
    "выявление потребностей": "needs_discovery",

    "presentation": "presentation",
    "product_presentation": "presentation",
    "презентация": "presentation",
    "презентация решения": "presentation",
    "презентация продукта": "presentation",

    "handling_questions": "handling_questions",
    "question_handling": "handling_questions",
    "работа с вопросами": "handling_questions",
    "обработка вопросов": "handling_questions",
    "обработка возражений": "handling_questions",

    "closing": "closing",
    "closure": "closing",
    "закрытие": "closing",
    "следующий шаг": "closing",

    "word_usage": "communication_style",
    "communication_style": "communication_style",
    "стиль речи": "communication_style",
    "коммуникация": "communication_style",

    "general": "general",
    "общая рекомендация": "general",
}

CATEGORY_TITLES = {
    "greeting": "Приветствие",
    "needs_assessment": "Выявление потребности",
    "needs_discovery": "Выявление потребности",
    "presentation": "Презентация решения",
    "product_presentation": "Презентация решения",
    "handling_questions": "Работа с вопросами",
    "closing": "Закрытие",
    "closure": "Закрытие",
    "word_usage": "Стиль речи",
    "general": "Общая рекомендация",
}

CATEGORY_IMPORTANCE = {
    "greeting": "Сильное начало разговора формирует доверие и задает тон всему звонку.",
    "needs_assessment": "Без выявления потребностей предложение звучит слишком общо и хуже попадает в запрос клиента.",
    "needs_discovery": "Без выявления потребностей предложение звучит слишком общо и хуже попадает в запрос клиента.",
    "presentation": "Клиенту проще увидеть ценность продукта, когда он связан с его задачами.",
    "product_presentation": "Клиенту проще увидеть ценность продукта, когда он связан с его задачами.",
    "handling_questions": "Качественная работа с вопросами помогает снять сомнения и продвинуть клиента дальше по воронке.",
    "closing": "Без четкого завершения звонок не приводит к следующему шагу.",
    "closure": "Без четкого завершения звонок не приводит к следующему шагу.",
    "word_usage": "Четкая и уверенная речь повышает доверие и делает аргументацию сильнее.",
    "general": "Эта рекомендация поможет сделать разговор более структурным и результативным.",
}

def _canonical_category(value) -> str:
    text = _clean_str(value).casefold()
    return CATEGORY_ALIASES.get(text, "general")

def _normalize_stage_list(stages):
    normalized = []

    for item in _as_list(stages):
        if not isinstance(item, dict):
            continue

        stage = _clean_str(item.get("stage")) or "—"
        found = bool(item.get("found", False))

        replicas = item.get("replicas")
        if replicas is None:
            replicas = item.get("quotes")
        replicas = [_clean_str(x) for x in _as_list(replicas) if _clean_str(x)]

        normalized.append({
            "stage": stage,
            "found": found,
            "replicas": replicas,
        })

    return normalized

def _normalize_missing_stages(raw_script, script_check_result):
    source = (
        raw_script.get("missing_stages")
        or script_check_result.get("missed_stages")
        or []
    )

    result = []
    for item in _as_list(source):
        parsed = item

        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            try:
                literal = ast.literal_eval(text)
                if isinstance(literal, dict):
                    parsed = literal
                else:
                    parsed = text
            except Exception:
                parsed = text

        if isinstance(parsed, dict):
            stage_name = _clean_str(parsed.get("stage"))
            if stage_name:
                result.append(stage_name)
        else:
            text = _clean_str(parsed)
            if text:
                result.append(text)

    # убираем дубли, сохраняя порядок
    unique = []
    seen = set()
    for item in result:
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique

def _normalize_violations(raw_script, script_check_result):
    source = raw_script.get("violations")
    if not _has_content(source):
        source = script_check_result.get("violations", []) or []

    return [_clean_str(x) for x in _as_list(source) if _clean_str(x)]

def _normalize_mistakes(raw_mistakes, manager_errors_result):
    source = raw_mistakes
    if not _has_content(source):
        source = manager_errors_result.get("errors", []) or []

    normalized = []
    for item in _as_list(source):
        if not isinstance(item, dict):
            text = _clean_str(item)
            if not text:
                continue
            normalized.append({
                "type": "",
                "quote": "",
                "description": text,
            })
            continue

        normalized.append({
            "type": _clean_str(item.get("type")),
            "quote": _clean_str(item.get("quote")),
            "description": _first_nonempty_str(
                item.get("description"),
                item.get("explanation"),
                item.get("text"),
            ),
        })

    return normalized

def _normalize_main_errors(raw_main_errors, raw_meta, mistakes):
    source = raw_main_errors
    if not _has_content(source):
        source = raw_meta.get("main_errors")

    result = []
    for item in _as_list(source):
        if isinstance(item, dict):
            text = _first_nonempty_str(
                item.get("description"),
                item.get("explanation"),
                item.get("quote"),
                item.get("type"),
            )
        else:
            text = _clean_str(item)

        if text:
            result.append(text)

    if result:
        return result

    # fallback: если main_errors отдельно не пришли, берем из mistakes
    for item in mistakes:
        text = _first_nonempty_str(item.get("description"), item.get("type"))
        if text:
            result.append(text)

    return result

def _normalize_recommendation_item(item):
    parsed = item

    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None

        try:
            literal = ast.literal_eval(text)
            if isinstance(literal, dict):
                parsed = literal
            else:
                parsed = {"text": text}
        except Exception:
            parsed = {"text": text}

    if not isinstance(parsed, dict):
        text = _clean_str(parsed)
        if not text:
            return None
        parsed = {"text": text}

    raw_type = _first_nonempty_str(parsed.get("type"))
    raw_category = _first_nonempty_str(parsed.get("category"), raw_type, "general")

    text = _first_nonempty_str(
        parsed.get("text"),
        parsed.get("recommendation"),
        parsed.get("suggested_text"),
        parsed.get("focus"),
        parsed.get("suggestion"),
        parsed.get("suggestedText"),
        parsed.get("description"),
    )
    if not text:
        return None

    canonical = _canonical_category(raw_category)

    return {
        "type": raw_type or canonical,
        "category": canonical,
        "text": text,
        "zone_of_growth": CATEGORY_TITLES.get(canonical, CATEGORY_TITLES["general"]),
        "why_important": CATEGORY_IMPORTANCE.get(canonical, CATEGORY_IMPORTANCE["general"]),
        "what_to_improve": text,
    }

def _normalize_recommendations(raw_recommendations, coaching_result):
    source = raw_recommendations
    if not source:
        source = coaching_result.get("recommendations", []) or []

    normalized = []
    seen_categories = set()
    seen_texts = set()

    for item in _as_list(source):
        rec = _normalize_recommendation_item(item)
        if not rec:
            continue

        text_key = rec["text"].strip().casefold()
        cat_key = rec["category"].strip().casefold()

        if text_key in seen_texts:
            continue

        # если уже была рекомендация для этой же зоны роста,
        # вторую добавляем только если текст заметно отличается и категория general не захватывает всё подряд
        if cat_key in seen_categories and cat_key != "general":
            continue

        seen_texts.add(text_key)
        seen_categories.add(cat_key)
        normalized.append(rec)

    return normalized

def _normalize_summary(raw, raw_summary, classification_result, structure_result, raw_script, script_check_result):
    if isinstance(raw_summary, dict):
        short_summary = _first_nonempty_str(
            raw_summary.get("short_summary"),
            raw_summary.get("summary"),
        )
        result_text = _first_nonempty_str(raw_summary.get("result"))
    else:
        short_summary = _clean_str(raw_summary)
        result_text = ""

    short_summary = _first_nonempty_str(
        short_summary,
        classification_result.get("short_summary"),
        classification_result.get("summary"),
        structure_result.get("summary"),
    )

    result_text = _first_nonempty_str(
        raw.get("conclusion"),
        result_text,
        classification_result.get("reason"),
    )

    if not result_text:
        result_text = "Итог звонка не сформирован."

    if not short_summary:
        short_summary = result_text

    return {
        "short_summary": short_summary,
        "result": result_text,
    }

def _normalize_final_report(result: dict) -> dict:
    raw = _as_dict(result.get("final_report"))

    classification_result = _as_dict(result.get("classification_result"))
    structure_result = _as_dict(result.get("structure_result"))
    script_check_result = _as_dict(result.get("script_check_result"))
    manager_errors_result = _as_dict(
        result.get("manager_errors_result") or result.get("errors_result")
    )
    coaching_result = _as_dict(result.get("coaching_result"))

    raw_summary = raw.get("summary")
    raw_script = _as_dict(raw.get("script_analysis"))
    raw_meta = _as_dict(raw.get("meta"))

    summary = _normalize_summary(
        raw=raw,
        raw_summary=raw_summary,
        classification_result=classification_result,
        structure_result=structure_result,
        raw_script=raw_script,
        script_check_result=script_check_result,
    )

    score = _pick_score(
        raw_script.get("followed_score"),
        script_check_result.get("score"),
        raw_meta.get("raw_score"),
        raw.get("score"),
    )

    dialog_stages = _normalize_stage_list(
        raw.get("dialog_stages") or raw.get("stages") or structure_result.get("stages") or []
    )

    missing_stages = _normalize_missing_stages(raw_script, script_check_result)
    violations = _normalize_violations(raw_script, script_check_result)

    script_analysis = {
        "followed_score": score,
        "missing_stages": missing_stages,
        "violations": violations,
        "comment": _first_nonempty_str(
            raw_script.get("comment"),
            script_check_result.get("comment"),
        ),
    }

    mistakes = _normalize_mistakes(raw.get("mistakes"), manager_errors_result)

    recommendations = _normalize_recommendations(
        raw.get("recommendations"),
        coaching_result,
    )

    main_errors = _normalize_main_errors(
        raw.get("main_errors"),
        raw_meta,
        mistakes,
    )

    training_focus = [
        _clean_str(x)
        for x in _as_list(raw_meta.get("training_focus") or coaching_result.get("training_focus"))
        if _clean_str(x)
    ]

    return {
        "summary": summary,
        "dialog_stages": dialog_stages,
        "script_analysis": script_analysis,
        "mistakes": mistakes,
        "recommendations": recommendations,
        "meta": {
            "main_errors": main_errors,
            "training_focus": training_focus,
            "raw_score": score,
        },
    }

def _build_error_result(call_id: str, transcript: str) -> dict:
    return {
        "call_id": call_id,
        "transcript": transcript,
        "usage": {},
        "llm_raw_result": {},
        "classification_result": {},
        "structure_result": {},
        "script_check_result": {},
        "manager_errors_result": {},
        "coaching_result": {},
        "final_report": {
            "summary": {
                "short_summary": "—",
                "result": "Ошибка анализа",
            },
            "dialog_stages": [],
            "script_analysis": {
                "followed_score": 0,
                "missing_stages": [],
                "violations": [],
                "comment": "",
            },
            "mistakes": [],
            "recommendations": [],
            "meta": {
                "main_errors": [],
                "training_focus": [],
                "raw_score": 0,
            },
        },
    }

def run_analysis_pipeline(call_id: str, transcript: str) -> dict:
    result = (
        run_llm_analysis(call_id=call_id, transcript=transcript, debug=True)
        if USE_LLM_PIPELINE
        else run_stub_pipeline(call_id=call_id, transcript=transcript)
    )

    if not isinstance(result, dict):
        return _build_error_result(call_id=call_id, transcript=transcript)

    result["call_id"] = result.get("call_id", call_id)
    result["transcript"] = result.get("transcript", transcript)
    result["usage"] = _as_dict(result.get("usage") or result.get("total_usage"))

    result["final_report"] = _normalize_final_report(result)

    print("=== FINAL REPORT AFTER PIPELINE NORMALIZATION ===")
    try:
        import json
        print(json.dumps(result["final_report"], ensure_ascii=False, indent=2))
    except Exception:
        print(result["final_report"])

    return result