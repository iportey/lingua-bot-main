"""Smoke-проверка проекта. Запуск: python smoke_test.py"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


async def run_checks() -> int:
    errors: list[str] = []

    if not Path(".env").exists():
        errors.append("Нет файла .env")
    else:
        load_dotenv()
        if not os.getenv("VK_TOKEN"):
            errors.append("VK_TOKEN не задан в .env")

    try:
        from app.db.session import SessionLocal, init_db
        from app.db import repository

        await init_db()
    except Exception as exc:
        errors.append(f"БД не инициализирована: {exc}")
        _report(errors)
        return 1

    try:
        from app.db.models import User
        from sqlalchemy import delete
        
        test_id = 999_999_999
        async with SessionLocal() as session:
            await session.execute(delete(User).where(User.vk_id == test_id))
            await session.commit()
            await repository.add_score(session, test_id, 10)
            
        async with SessionLocal() as session:
            score = await repository.get_score(session, test_id)
            
        if score != 10:
            errors.append(f"БД не сохраняет счет пользователя (score={score})")
    except Exception as exc:
        errors.append(f"Тест БД: {exc}")

    try:
        from app.domain import content

        assert len(content.FLASHCARDS) > 0
        assert len(content.QUIZZES) > 0
        
        cards = content.get_all_cards("Food")
        assert len(cards) >= 20
        
        q = content.get_random_question("Easy")
        assert "q" in q and "options" in q
    except Exception as exc:
        errors.append(f"Контент: {exc}")

    if errors:
        _report(errors)
        return 1

    print("Все проверки пройдены")
    return 0


def _report(errors: list[str]) -> None:
    print("Обнаружены проблемы:")
    for err in errors:
        print(f"  - {err}")


if __name__ == "__main__":
    sys.exit(asyncio.run(run_checks()))