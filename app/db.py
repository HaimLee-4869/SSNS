from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.config import settings

SELF_AUTHOR = "나"


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
                author_name TEXT NOT NULL DEFAULT '나',
                transcript TEXT NOT NULL,
                refined_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(posts)")}
        if "author_name" not in columns:
            conn.execute(f"ALTER TABLE posts ADD COLUMN author_name TEXT NOT NULL DEFAULT '{SELF_AUTHOR}'")


def insert_post(transcript: str, refined_text: str, author_name: str = SELF_AUTHOR) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (author_name, transcript, refined_text, created_at) VALUES (?, ?, ?, ?)",
            (author_name, transcript, refined_text, created_at),
        )
        return {
            "id": cursor.lastrowid,
            "author_name": author_name,
            "transcript": transcript,
            "refined_text": refined_text,
            "created_at": created_at,
        }


def list_posts(limit: int = 50, author: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if author:
            rows = conn.execute(
                "SELECT id, author_name, transcript, refined_text, created_at FROM posts "
                "WHERE author_name = ? ORDER BY created_at DESC LIMIT ?",
                (author, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, author_name, transcript, refined_text, created_at FROM posts "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]


def get_latest_post_by_author(name: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, author_name, transcript, refined_text, created_at FROM posts "
            "WHERE author_name LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"%{name}%",),
        ).fetchone()
        return dict(row) if row else None


def get_last_post_at(author: str = SELF_AUTHOR) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT created_at FROM posts WHERE author_name = ? ORDER BY created_at DESC LIMIT 1",
            (author,),
        ).fetchone()
        return row["created_at"] if row else None
