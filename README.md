AI Call Analyzer - RAG модуль

Ветка с реализацией RAG (Retrieval-Augmented Generation) для анализа звонков.

Что сделано
- Индексация текстовых файлов знаний в ChromaDB
- Разбиение на чанки с перекрытием
- Поиск релевантных чанков по запросу
- Фильтрация по порогу похожести
- Возврат метаданных (источник знаний)

Файлы знаний
- `stages.txt` - этапы звонка
- `script.txt` - эталонный скрипт
- `criteria.txt` - критерии ошибок
- `coach_tips.txt` - рекомендации

Реализация RAG
- файлы знаний разбиваются на чанки по предложениям
- каждый чанк превращается в эмбеддинг через модель `multilingual-e5-small`
- эмбеддинги хранятся в ChromaDB
- при запросе текст звонка тоже превращается в эмбеддинг и ищутся похожие чанки
- найденные чанки отдаются в GigaChat вместе с транскриптом

Использование
from app.llm_module.rag import retrieve_knowledge

chunks, metadata = retrieve_knowledge(
    query="текст звонка",
    top_k=3,
    filter_type="coach_tips"
)

Зависимости:
chromadb
sentence-transformers
nltk