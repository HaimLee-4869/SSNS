from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import db
from app.config import settings
from app.services import openai_client
from app.services.agent import SSNSAgent

app = FastAPI(title=settings.app_name, version="0.1.0")
agent = SSNSAgent()
db.init_db()


class VoiceInput(BaseModel):
    transcript: str


class TTSInput(BaseModel):
    text: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/v1/posts/refine")
def refine_post(payload: VoiceInput) -> dict:
    return {"refined_post": agent.refine_post(payload.transcript)}


@app.post("/api/v1/posts/summarize")
def summarize_post(payload: VoiceInput) -> dict:
    return {"summary": agent.summarize_day(payload.transcript)}


@app.post("/api/v1/posts/voice")
async def create_post_from_voice(audio: UploadFile = File(...)) -> dict:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

    try:
        transcript = openai_client.transcribe_audio(audio_bytes, audio.filename or "voice.webm")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"음성 인식 실패: {exc}") from exc

    refined = agent.refine_post(transcript)
    return db.insert_post(transcript=transcript, refined_text=refined)


@app.get("/api/v1/posts")
def get_posts(author: str | None = None) -> list[dict]:
    return db.list_posts(author=author)


@app.get("/api/v1/posts/by-author")
def get_post_by_author(name: str) -> dict:
    post = db.get_latest_post_by_author(name)
    if post is None:
        raise HTTPException(status_code=404, detail=f"'{name}'님의 소식을 찾을 수 없어요.")
    return post


@app.post("/api/v1/voice/intent")
async def classify_voice_intent(audio: UploadFile = File(...)) -> dict:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="빈 오디오 파일입니다.")

    try:
        transcript = openai_client.transcribe_audio(audio_bytes, audio.filename or "voice.webm")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"음성 인식 실패: {exc}") from exc

    intent_result = agent.classify_intent(transcript)
    return {"transcript": transcript, **intent_result}


@app.get("/api/v1/status")
def get_status() -> dict:
    last_post_at = db.get_last_post_at()
    if last_post_at is None:
        return {
            "status": "waiting",
            "label": "대기중",
            "days_since": None,
            "message": "아직 첫 기록이 없어요.",
        }

    last_dt = datetime.fromisoformat(last_post_at)
    days_since = (datetime.now(timezone.utc) - last_dt).days

    if days_since <= 0:
        return {"status": "normal", "label": "정상", "days_since": days_since, "message": "오늘 활동을 기록했어요."}
    if days_since <= 2:
        return {
            "status": "caution",
            "label": "관찰",
            "days_since": days_since,
            "message": "최근 활동 기록이 뜸해요.",
        }
    return {
        "status": "danger",
        "label": "경고",
        "days_since": days_since,
        "message": f"{days_since}일째 기록이 없어요. 안부를 확인해주세요.",
    }


@app.post("/api/v1/tts")
def text_to_speech(payload: TTSInput) -> Response:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    try:
        audio_bytes = openai_client.synthesize_speech(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"음성 합성 실패: {exc}") from exc
    return Response(content=audio_bytes, media_type="audio/mpeg")


app.mount("/", StaticFiles(directory="static", html=True), name="static")
