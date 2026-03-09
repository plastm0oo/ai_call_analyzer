from app.agents.base_agent import BaseAgent


class MistakesAgent(BaseAgent):
    def run(self, data: dict) -> dict:
        mistakes = [
            {
                "type": "Не завершил звонок целевым действием",
                "description": "Менеджер не предложил следующий шаг: встречу, демо или повторный звонок."
            },
            {
                "type": "Недостаточная глубина выявления потребности",
                "description": "Менеджер слишком рано перешёл к презентации, не уточнив детали задачи клиента."
            }
        ]

        data["mistakes"] = mistakes
        return data