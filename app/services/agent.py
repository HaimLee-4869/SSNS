from __future__ import annotations

from app.config import settings
from app.services import openai_client


class SSNSAgent:
    """Voice-to-post agent for the SSNS concept."""

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
