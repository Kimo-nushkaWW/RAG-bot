RAG Bot on Local Models

## Возможности
- Загрузка текстовых документов
- Разбиение на чанки с перекрытием
- Векторный поиск по документам (ChromaDB + Ollama embeddings)
- Ответы на вопросы с использованием локальной LLM (llama3.2)
- REST API на FastAPI

## Требования
- Python 3.10+
- Установленный Ollama (https://ollama.com)
- Загруженные модели: `nomic-embed-text`, `llama3.2`(ollama pull llama3.2 && ollama pull nomic-embed-text)

## Установка и запуск
1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Запустите сервер: `uvicorn main:app --reload`
4. Запустите визуал: `streamlit run app.py`
5. Откройте http://localhost:8501

## Структура проекта
- app.py - Отвечает за графический интерфейс
- main.py - Отвечает за работу функций

## Автор
Telegram: @kimowww
