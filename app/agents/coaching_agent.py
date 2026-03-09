from app.agents.base_agent import BaseAgent


class CoachingAgent(BaseAgent):
    def run(self, data: dict) -> dict:
        recommendations = [
            {
                "problem": "Недостаточная глубина выявления потребности",
                "reason": "Без уточняющих вопросов менеджер не понимает точную боль клиента.",
                "recommendation": "Добавить 2–3 открытых вопроса перед презентацией."
            },
            {
                "problem": "Нет закрытия на следующий шаг",
                "reason": "Звонок заканчивается без понятного продолжения, что снижает шанс конверсии.",
                "recommendation": "В конце каждого звонка предлагать конкретный следующий шаг."
            }
        ]

        data["coaching_recommendations"] = recommendations
        return data