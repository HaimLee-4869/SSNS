from __future__ import annotations

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None

REFINE_SYSTEM_PROMPT = (
    "당신은 어르신이 말한 하루 일과를 따뜻하고 자연스러운 SNS 게시글로 다듬는 도우미입니다. "
    "1~3문장, 친근한 존댓말을 사용하고 이모지는 최대 1개만 사용하세요. "
    "말하지 않은 내용을 지어내거나 과장하지 마세요."
)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    client = get_client()
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, file_bytes),
    )
    return response.text.strip()


def refine_text(transcript: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": REFINE_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def synthesize_speech(text: str) -> bytes:
    client = get_client()
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    return response.content
