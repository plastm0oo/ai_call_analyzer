import json

from app.llm_module.agents import GigaChatAgentPipeline
from app.llm_module.utils import load_text

transcript = """
Менеджер: Добрый день, меня зовут Анна, компания Альфа. Вам удобно говорить?
Клиент: Да, удобно.
Менеджер: Подскажите, как вы сейчас контролируете качество звонков?
Клиент: Пока вручную, слушаем выборочно.
Менеджер: У нас есть решение, которое автоматически анализирует звонки и показывает ошибки менеджеров.
Клиент: А внедрение сложное?
Менеджер: Нет, можно начать с пилота на небольшой группе.
Менеджер: Давайте я отправлю материалы и мы созвонимся завтра.
"""

pipeline = GigaChatAgentPipeline()

from export_report import export_report, export_text_report

result = pipeline.run_pipeline(
    transcript=transcript,
    stages_text=load_text("knowledge/stages.txt"),
    script_text=load_text("knowledge/script.txt"),
    criteria_text=load_text("knowledge/criteria.txt"),
    coach_tips_text=load_text("knowledge/coach_tips.txt")
)

export_report(result)
export_text_report(result)