"""'OO의 소식 알려줘' 시나리오를 시연하기 위한 가족/지인 데모 게시물을 추가합니다."""
from __future__ import annotations

from app import db

DEMO_POSTS = [
    ("손주", "오늘 놀이터에서 신나게 뛰어놀았어요! 할머니 보고 싶어요 😊"),
    ("이웃", "오늘은 경로당에서 이웃들과 화투 치며 즐거운 시간을 보냈어요."),
]


def main() -> None:
    db.init_db()
    for author_name, refined_text in DEMO_POSTS:
        db.insert_post(transcript=refined_text, refined_text=refined_text, author_name=author_name)
    print(f"{len(DEMO_POSTS)}개의 데모 게시물을 추가했습니다.")


if __name__ == "__main__":
    main()
