from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import time
from typing import Optional

app = FastAPI(title="ML Service for Answer Checking")


class AnswerCheckRequest(BaseModel):
    question: str
    correct_answer: str
    user_answer: str


class AnswerCheckResponse(BaseModel):
    is_correct: int
    processing_time: float
    error: Optional[str] = None


@app.post("/check_answer", response_model=AnswerCheckResponse)
async def check_answer(request: AnswerCheckRequest):
    """
        Проверяет ответ пользователя.
        В 1 случае из 3 возвращает ошибку 503.
        Имитирует задержку LLM (5 секунд)
    """
    delay = random.uniform(5.0, 8.0)
    time.sleep(delay)
    
    error_roll = random.randint(1, 3) # рандомайзим
    if error_roll == 1:
        raise HTTPException(
            status_code=503,
            detail="LLM service temporarily unavailable"
        )
    
    def normalize(text: str) -> str:
        return text.lower().strip().replace('.', '').replace(',', '').replace('!', '').replace('?', '')
    
    user_normalized = normalize(request.user_answer)
    correct_normalized = normalize(request.correct_answer)
    
    is_correct = 1 if (correct_normalized in user_normalized or user_normalized in correct_normalized) else 0

    if not is_correct and len(user_normalized) > 10:
        correct_words = set(correct_normalized.split())
        user_words = set(user_normalized.split())
        if len(correct_words & user_words) / len(correct_words) > 0.6:
            is_correct = 1
    
    return AnswerCheckResponse(
        is_correct=is_correct,
        processing_time=delay
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "ML Service for Answer Checking is running"}
