from app.agents.base_agent import BaseAgent


class StructuralAgent(BaseAgent):
    def run(self, data: dict) -> dict:
        transcript = data["transcript"]

        stages = [
            {
                "stage": "Приветствие",
                "replicas": [
                    "Менеджер: Добрый день! Меня зовут Анна, компания Альфа."
                ]
            },
            {
                "stage": "Уточнение удобства разговора",
                "replicas": [
                    "Менеджер: Подскажите, пожалуйста, удобно сейчас говорить?",
                    "Клиент: Да, удобно."
                ]
            },
            {
                "stage": "Выявление потребности",
                "replicas": [
                    "Менеджер: Хотела уточнить, интересует ли вас автоматизация продаж?",
                    "Клиент: Да, расскажите подробнее."
                ]
            },
            {
                "stage": "Презентация",
                "replicas": [
                    "Менеджер: У нас есть решение, которое помогает анализировать звонки и повышать конверсию."
                ]
            }
        ]

        data["dialog_structure"] = [
            {"stage": "Приветствие", "replicas": ["..."]},
            {"stage": "Выявление потребности", "replicas": ["..."]}
        ]

        return data