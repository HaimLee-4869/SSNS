from __future__ import annotations

import re

from app.config import settings
from app.services import openai_client

VALID_INTENTS = {"write_post", "query_news", "end", "unknown"}

_END_KEYWORDS = ("아니요", "아니", "괜찮아", "없어", "됐어", "그만")
_NEWS_KEYWORDS = ("소식", "안부", "잘 지내")
_WRITE_KEYWORDS = ("쓸래", "쓰고", "써줘", "게시", "올릴래", "적을래")
_NEWS_TARGET_PATTERN = re.compile(r"([가-힣]+)(?:의|이|가)?\s*소식")


class SSNSAgent:
    """Voice-to-post agent for the SSNS concept."""

    def classify_intent(self, transcript: str) -> dict:
        text = (transcript or "").strip()

        if settings.openai_api_key:
            try:
                result = openai_client.classify_intent(text)
                if result.get("intent") in VALID_INTENTS:
                    return result
            except Exception:
                pass

        if any(keyword in text for keyword in _END_KEYWORDS):
            return {"intent": "end", "target_name": None}
        if any(keyword in text for keyword in _NEWS_KEYWORDS):
            match = _NEWS_TARGET_PATTERN.search(text)
            return {"intent": "query_news", "target_name": match.group(1) if match else None}
        if any(keyword in text for keyword in _WRITE_KEYWORDS):
            return {"intent": "write_post", "target_name": None}
        return {"intent": "unknown", "target_name": None}

    def refine_post(self, transcript: str) -> str:
        text = " ".join((transcript or "").strip().split())
        if not text:
            return "오늘은 조용히 하루를 보내고 있었어요."

        if settings.openai_api_key:
            try:
                return openai_client.refine_text(text)
            except Exception:
                pass

        cleaned = text if text.endswith((".", "!", "?")) else f"{text}."
        return f"오늘의 기록: {cleaned}"

    def summarize_day(self, transcript: str) -> str:
        refined = self.refine_post(transcript)
        return f"{refined} 오늘도 한 걸음씩 활기찬 하루를 보냈어요."
