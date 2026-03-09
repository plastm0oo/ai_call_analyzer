import json
import re
from typing import Any, Dict, List

from app.llm_module.gigachat_client import GigaChatClient


class GigaChatAgentPipeline:
    def __init__(self, debug: bool = True) -> None:
        self.client = GigaChatClient()
        self.debug = debug
        self.total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    def _add_usage(self, usage: Dict[str, Any]) -> None:
        self.total_usage["prompt_tokens"] += int(usage.get("prompt_tokens", 0) or 0)
        self.total_usage["completion_tokens"] += int(usage.get("completion_tokens", 0) or 0)
        self.total_usage["total_tokens"] += int(usage.get("total_tokens", 0) or 0)

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        result = self.client.ask(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        usage = result.get("usage", {})
        self._add_usage(usage)

        if self.debug:
            print("\n=== LLM RAW OUTPUT ===")
            print(result.get("content", ""))

        return result

    def _normalize_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _extract_manager_lines(self, transcript: str) -> str:
        lines = []
        for raw_line in transcript.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith("менеджер:") or lower.startswith("manager:"):
                lines.append(line)

        return "\n".join(lines) if lines else transcript

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Пытается достать JSON максимально терпимо.
        """
        text = text.strip()

        # 1. Если модель вернула ```json ... ```
        code_block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()

        # 2. Пробуем как есть
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 3. Вырезаем участок от первой { до последней }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
            raise ValueError(f"Не удалось найти JSON-объект в ответе модели:\n{text}")

        candidate = text[first_brace:last_brace + 1]

        # 4. Пробуем candidate как есть
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # 5. Мини-очистка
        cleaned = candidate
        cleaned = cleaned.replace("\r", " ").replace("\n", " ")
        cleaned = cleaned.replace("“", '"').replace("”", '"')
        cleaned = cleaned.replace("‘", "'").replace("’", "'")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON не распарсился даже после очистки: {e}\nRAW:\n{text}\n\nCLEANED:\n{cleaned}")

    def _repair_json_with_llm(self, broken_text: str) -> Dict[str, Any]:
        """
        Если модель вернула кривой JSON — просим её переписать ответ в валидный JSON
        без изменения смысла.
        """
        system_prompt = """
Ты исправляешь формат JSON.

Тебе дадут текст, который должен быть JSON, но он может быть сломан.
Нужно вернуть только валидный JSON без markdown, без комментариев, без пояснений.
Нельзя менять смысл данных.
Ответ должен начинаться с { и заканчиваться }.
""".strip()

        user_prompt = f"""
Исправь в валидный JSON этот текст:

{broken_text}
""".strip()

        llm_result = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=900
        )

        return self._extract_json(llm_result["content"])

    def _safe_parse_or_repair_json(self, text: str) -> Dict[str, Any]:
        """
        Сначала пробует обычный парсинг.
        Если не вышло — автопочинка через отдельный вызов модели.
        """
        try:
            return self._extract_json(text)
        except Exception as first_error:
            if self.debug:
                print("\n=== JSON PARSE FAILED, TRYING REPAIR ===")
                print(first_error)

            try:
                return self._repair_json_with_llm(text)
            except Exception as second_error:
                raise ValueError(
                    f"Не удалось распарсить JSON и не удалось починить его через LLM.\n"
                    f"Первичная ошибка: {first_error}\n"
                    f"Ошибка починки: {second_error}"
                )

    def agent_1_structure(self, transcript: str, stages_text: str) -> Dict[str, Any]:
        system_prompt = """
Ты анализируешь продажный звонок.

Нужно:
1. Разметить звонок по этапам.
2. Отметить, найден этап или нет.
3. Привести короткие цитаты.

Верни только валидный JSON.
Без markdown.
Без пояснений.
Ответ должен начинаться с { и заканчиваться }.

Формат:
{
  "summary": "...",
  "stages": [
    {
      "stage": "Приветствие",
      "found": true,
      "quotes": ["..."]
    }
  ]
}
""".strip()

        user_prompt = f"""
Этапы:
{stages_text}

Транскрипт:
{transcript}
""".strip()

        llm_result = self._call_llm(system_prompt, user_prompt, max_tokens=900)
        result = self._safe_parse_or_repair_json(llm_result["content"])

        result.setdefault("summary", "")
        result.setdefault("stages", [])

        normalized_stages = []
        for item in result["stages"]:
            if not isinstance(item, dict):
                continue
            normalized_stages.append({
                "stage": str(item.get("stage", "")).strip(),
                "found": bool(item.get("found", False)),
                "quotes": self._normalize_list(item.get("quotes", []))
            })

        result["summary"] = str(result["summary"]).strip()
        result["stages"] = normalized_stages
        result["usage"] = llm_result.get("usage", {})

        return result

    def agent_2_script_check(
        self,
        script_text: str,
        structure_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_prompt = """
Ты проверяешь, насколько звонок соответствует скрипту продаж.

Найди:
- пропущенные этапы
- нарушения
- общую оценку от 0 до 100

Верни только валидный JSON.
Без markdown.
Без пояснений.
Ответ должен начинаться с { и заканчиваться }.

Формат:
{
  "score": 0,
  "missed_stages": [],
  "violations": [],
  "comment": "..."
}
""".strip()

        user_prompt = f"""
Скрипт:
{script_text}

Разметка звонка:
{json.dumps(structure_result, ensure_ascii=False, indent=2)}
""".strip()

        llm_result = self._call_llm(system_prompt, user_prompt, max_tokens=700)
        result = self._safe_parse_or_repair_json(llm_result["content"])

        result.setdefault("score", 0)
        result.setdefault("missed_stages", [])
        result.setdefault("violations", [])
        result.setdefault("comment", "")

        try:
            result["score"] = int(result["score"])
        except Exception:
            result["score"] = 0

        result["score"] = max(0, min(100, result["score"]))
        result["missed_stages"] = self._normalize_list(result["missed_stages"])
        result["violations"] = self._normalize_list(result["violations"])
        result["comment"] = str(result["comment"]).strip()
        result["usage"] = llm_result.get("usage", {})

        return result

    def agent_3_manager_errors(
        self,
        transcript: str,
        criteria_text: str
    ) -> Dict[str, Any]:
        system_prompt = """
Ты анализируешь только речь менеджера.

Найди:
- слабые формулировки
- ошибки коммуникации
- пропущенные действия

Верни только валидный JSON.
Без markdown.
Без пояснений.
Ответ должен начинаться с { и заканчиваться }.

Формат:
{
  "errors": [
    {
      "type": "...",
      "quote": "...",
      "explanation": "..."
    }
  ],
  "strengths": []
}
""".strip()

        manager_only = self._extract_manager_lines(transcript)

        user_prompt = f"""
Критерии ошибок:
{criteria_text}

Реплики менеджера:
{manager_only}
""".strip()

        llm_result = self._call_llm(system_prompt, user_prompt, max_tokens=900)
        result = self._safe_parse_or_repair_json(llm_result["content"])

        result.setdefault("errors", [])
        result.setdefault("strengths", [])

        normalized_errors = []
        for err in result["errors"]:
            if not isinstance(err, dict):
                continue
            normalized_errors.append({
                "type": str(err.get("type", "")).strip(),
                "quote": str(err.get("quote", "")).strip(),
                "explanation": str(err.get("explanation", "")).strip()
            })

        result["errors"] = normalized_errors
        result["strengths"] = self._normalize_list(result["strengths"])
        result["usage"] = llm_result.get("usage", {})

        return result

    def agent_4_coaching(
        self,
        errors_result: Dict[str, Any],
        coach_tips_text: str
    ) -> Dict[str, Any]:
        system_prompt = """
Ты коуч по продажам.

По найденным ошибкам дай рекомендации для следующего звонка.

Верни только валидный JSON.
Без markdown.
Без пояснений.
Ответ должен начинаться с { и заканчиваться }.

Формат:
{
  "recommendations": [],
  "training_focus": []
}
""".strip()

        user_prompt = f"""
Шаблоны рекомендаций:
{coach_tips_text}

Ошибки менеджера:
{json.dumps(errors_result, ensure_ascii=False, indent=2)}
""".strip()

        llm_result = self._call_llm(system_prompt, user_prompt, max_tokens=700)
        result = self._safe_parse_or_repair_json(llm_result["content"])

        result.setdefault("recommendations", [])
        result.setdefault("training_focus", [])

        result["recommendations"] = self._normalize_list(result["recommendations"])
        result["training_focus"] = self._normalize_list(result["training_focus"])
        result["usage"] = llm_result.get("usage", {})

        return result

    def agent_5_final_report(
        self,
        structure_result: Dict[str, Any],
        script_check_result: Dict[str, Any],
        errors_result: Dict[str, Any],
        coaching_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        system_prompt = """
Собери итоговый отчёт по звонку.

Верни только валидный JSON.
Без markdown.
Без пояснений.
Ответ должен начинаться с { и заканчиваться }.

Формат:
{
  "summary": "...",
  "score": 0,
  "main_errors": [],
  "recommendations": [],
  "conclusion": "..."
}
""".strip()

        user_prompt = f"""
Разметка:
{json.dumps(structure_result, ensure_ascii=False, indent=2)}

Проверка скрипта:
{json.dumps(script_check_result, ensure_ascii=False, indent=2)}

Ошибки менеджера:
{json.dumps(errors_result, ensure_ascii=False, indent=2)}

Рекомендации:
{json.dumps(coaching_result, ensure_ascii=False, indent=2)}
""".strip()

        llm_result = self._call_llm(system_prompt, user_prompt, max_tokens=800)
        result = self._safe_parse_or_repair_json(llm_result["content"])

        result.setdefault("summary", "")
        result.setdefault("score", script_check_result.get("score", 0))
        result.setdefault("main_errors", [])
        result.setdefault("recommendations", [])
        result.setdefault("conclusion", "")

        try:
            result["score"] = int(result["score"])
        except Exception:
            result["score"] = 0

        result["score"] = max(0, min(100, result["score"]))
        result["summary"] = str(result["summary"]).strip()
        result["main_errors"] = self._normalize_list(result["main_errors"])
        result["recommendations"] = self._normalize_list(result["recommendations"])
        result["conclusion"] = str(result["conclusion"]).strip()
        result["usage"] = llm_result.get("usage", {})

        return result

    def run_pipeline(
        self,
        transcript: str,
        stages_text: str,
        script_text: str,
        criteria_text: str,
        coach_tips_text: str
    ) -> Dict[str, Any]:
        self.total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        structure_result = self.agent_1_structure(transcript, stages_text)
        script_check_result = self.agent_2_script_check(script_text, structure_result)
        errors_result = self.agent_3_manager_errors(transcript, criteria_text)
        coaching_result = self.agent_4_coaching(errors_result, coach_tips_text)
        final_report = self.agent_5_final_report(
            structure_result=structure_result,
            script_check_result=script_check_result,
            errors_result=errors_result,
            coaching_result=coaching_result,
        )

        return {
            "structure_result": structure_result,
            "script_check_result": script_check_result,
            "errors_result": errors_result,
            "coaching_result": coaching_result,
            "final_report": final_report,
            "total_usage": self.total_usage
        }