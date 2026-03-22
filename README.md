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

🔧 Установка
1. Клонировать репозиторий
git clone <your-repo-url>
cd ai_call_analyzer
2. Установить зависимости backend
pip install fastapi uvicorn python-multipart
pip install openai-whisper torch
pip install nltk chromadb sentence-transformers
pip install python-docx reportlab
pip install requests python-dotenv
3. Установить ffmpeg
Windows:
winget install Gyan.FFmpeg

Проверка:

ffmpeg -version
4. Настроить переменные окружения

Создать файл .env в корне проекта:

GIGACHAT_AUTH_KEY=ВАШ_КЛЮЧ
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat-2-Pro
GIGACHAT_AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_API_URL=https://gigachat.devices.sberbank.ru/api/v1/chat/completions
5. Установить frontend
cd frontend
npm install
▶️ Запуск
Backend (из корня проекта)
uvicorn app.main:app --reload

Проверка:

http://127.0.0.1:8000/health
Frontend
cd frontend
npm run dev

Открой в браузере:

http://localhost:5173

(порт может отличаться — смотри в терминале)

📥 Использование
Загрузить .wav или .mp3 файл
Нажать "Запустить анализ"
Получить:
транскрипт
анализ этапов
оценку
ошибки
рекомендации
Скачать отчёт:
📄 Word
📕 PDF
📚 RAG (Retrieval-Augmented Generation)

Используется база знаний:

stages.txt — этапы звонка
script.txt — эталонный скрипт
criteria.txt — критерии ошибок
coach_tips.txt — рекомендации

Процесс:

разбиение на чанки
эмбеддинги (multilingual-e5-small)
хранение в ChromaDB
поиск релевантных фрагментов при анализе
⚠️ Важно
Не коммитить:
.env
uploads/
reports/
chroma_db/
.cache/
.idea/
__pycache__/
🐛 Возможные проблемы
❌ ffmpeg не найден
Speech-to-Text failed: WinError 2

👉 Установить ffmpeg

❌ Failed to fetch (frontend)

👉 Проверить CORS и порт frontend

❌ Долгая первая загрузка

👉 Модели Whisper и embeddings скачиваются впервые