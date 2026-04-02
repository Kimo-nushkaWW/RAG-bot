import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException, status
from chromadb.errors import ChromaError
from ollama import chat, ChatResponse, ResponseError
from pydantic import BaseModel
from typing import Optional
import httpx
import uuid

app = FastAPI()

#Создание коллекции ChromDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_functions.OllamaEmbeddingFunction(
        model_name="nomic-embed-text"
    )
)

#Создание модели
class document_upload(BaseModel):
    text: str
    doc_id: Optional[str] = None
    chunk_size: int = 500
    overlap: int = 50

#Создание функции разделения текста на чанки
def split_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end > len(text):
            end = len(text)
        chunk = text[start:end]
        chunks.append(chunk)
        start = start+(chunk_size-overlap)
    
    return chunks

#Добавление эндпоинта для загрузки текста
@app.post("/upload")
async def upload(data:document_upload):
    try:
        doc_id=data.doc_id
        if not doc_id or doc_id == "string":
            doc_id = str(uuid.uuid4())
        ids = []
        documents = []
        metadatas = []
        chunks = split_text(data.text, data.chunk_size, data.overlap)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"doc_id": doc_id, "chunk_index": i})
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return {
            "doc_id": doc_id,
            "chunks_amount": len(chunks)
        }
    except ChromaError as e:
        #Ошибка базы данных
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Ошибка базы данных: {e}")
    except ValueError as e:
        #Ошибка валидации данных
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Неверные данные: {e}")
    except Exception as e:
        #Любая другая непредвиденная ошибка
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {e}")

#Создание модели
class question(BaseModel):
    question: str
    n_results: int = 5

#Добавление эндпоинта для ответа на вопрос
@app.post("/ask")
async def asking(data:question):
    try:
        response = collection.query( query_texts=[data.question], n_results=data.n_results)
        chunks = response["documents"][0]
        if not chunks: #Проверка, если ничего не нашло, то запрос к ИИ не отправляется
            return {
                "Ответ": "Ничего не найдено"
            }
        else:
            united_chunks= "\n---\n".join(chunks) 
            response:   ChatResponse = chat(model='llama3.2', messages=[ #Вопрос к ИИ
                    {
                        "role":"user",
                        "content": f"Используй следующие фрагменты документов для ответа на вопрос.Если в них нет ответа, скажи, что не знаешь. Фрагменты: {united_chunks}. Вопрос: {data.question}"
                    },
                ])
            return {
                "Вопрос": data.question,
                "Ответ": response.message.content
            }
    #Ошбика на стороне ChromDB
    except ChromaError as e:
        raise HTTPException(status_code=503, detail=f"Ошибка векторной базы: {e}")
    #Ошбика Ollama
    except ResponseError as e:
        raise HTTPException(status_code=503, detail=f"Ошибка модели: {e}")
    #Остальные ошибки
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}")

#Эндпоинт для проверки работоспособности Ollama    
@app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0) # Отправляем GET-запрос к Ollama с таймаутом в 5 секунд
        if response.status_code == 200:
            return {"status": "healthy",
                     "ollama": "connected"}
        else:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Ollama вернул неожиданный статус: {response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Ollama не успел ответить за отведённое время")
    except httpx.ConnectError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось подключиться к Ollama. Убедитесь, что он запущен")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка при проверке здоровья:{e}")