from app.agents.base_agent import BaseAgent


class FinalReportAgent(BaseAgent):
    def run(self, data: dict) -> dict:
        summary = {
            "short_summary": (
                "Звонок был посвящён обсуждению интереса клиента к автоматизации продаж. "
                "Менеджер провёл приветствие, уточнил возможность разговора, кратко выявил интерес "
                "и презентовал решение. При этом не были полностью проработаны потребности клиента "
                "и отсутствовало закрытие на следующий шаг."
            ),
            "result": "Клиент проявил интерес, но звонок не завершён конкретной договорённостью."
        }

        data["final_report"] = {
            "summary": summary,
            "dialog_stages": data.get("dialog_structure", []),
            "script_analysis": data.get("script_analysis", {}),
            "mistakes": data.get("mistakes", []),
            "recommendations": data.get("coaching_recommendations", [])
        }
        return data