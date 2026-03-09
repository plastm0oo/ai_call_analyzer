from app.agents.base_agent import BaseAgent


class ScriptCheckAgent(BaseAgent):
    def run(self, data: dict) -> dict:
        required_stages = [
            "Приветствие",
            "Уточнение удобства разговора",
            "Выявление потребности",
            "Презентация",
            "Работа с возражениями",
            "Закрытие на следующий шаг"
        ]

        found_stages = [stage["stage"] for stage in data.get("dialog_structure", [])]

        missing_stages = [stage for stage in required_stages if stage not in found_stages]

        data["script_analysis"] = {
            "followed_score": max(0, 100 - len(missing_stages) * 15),
            "missing_stages": missing_stages,
            "violations": [
                f"Пропущен этап: {stage}" for stage in missing_stages
            ]
        }
        return data