from __future__ import annotations

import json

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None

REFINE_SYSTEM_PROMPT = (
    "당신은 어르신이 말한 하루 일과를 따뜻하고 자연스러운 SNS 게시글로 다듬는 도우미입니다. "
    "1~3문장, 친근한 존댓말을 사용하고 이모지는 최대 1개만 사용하세요. "
    "말하지 않은 내용을 지어내거나 과장하지 마세요."
)

INTENT_SYSTEM_PROMPT = (
    "사용자의 말을 듣고 의도를 분류하는 도우미입니다. 가능한 의도는 다음과 같습니다.\n"
    "- write_post: 오늘 있었던 일을 SNS에 게시하고 싶어하는 경우\n"
    "- query_news: 특정 사람(가족, 이웃 등)의 최근 소식을 듣고 싶어하는 경우\n"
    "- end: 더 이상 도움이 필요 없다고 말하는 경우 (예: 아니요, 괜찮아요, 없어요, 됐어요, 그만할래)\n"
    "- unknown: 위 세 가지에 해당하지 않는 경우\n"
    "query_news인 경우 target_name에 언급된 사람을 가리키는 단어(예: 손주, 손자, 딸, 이웃)를 추출하세요. "
    "그 외에는 target_name을 null로 두세요.\n"
    '다음 JSON 형식으로만 답하세요: {"intent": "write_post 또는 query_news 또는 end 또는 unknown", "target_name": "문자열 또는 null"}'
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


def classify_intent(transcript: str) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def synthesize_speech(text: str) -> bytes:
    client = get_client()
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    return response.content
