from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript TEXT NOT NULL,
                refined_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def insert_post(transcript: str, refined_text: str) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (transcript, refined_text, created_at) VALUES (?, ?, ?)",
            (transcript, refined_text, created_at),
        )
        return {
            "id": cursor.lastrowid,
            "transcript": transcript,
            "refined_text": refined_text,
            "created_at": created_at,
        }


def list_posts(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, transcript, refined_text, created_at FROM posts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_last_post_at() -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return row["created_at"] if row else None
