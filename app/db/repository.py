from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, User


async def get_or_create_user(session: AsyncSession, vk_id: int) -> User:
    result = await session.execute(select(User).where(User.vk_id == vk_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(vk_id=vk_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def add_score(session: AsyncSession, vk_id: int, points: int) -> None:
    user = await get_or_create_user(session, vk_id)
    user.score += points
    await session.commit()


async def get_score(session: AsyncSession, vk_id: int) -> int:
    user = await get_or_create_user(session, vk_id)
    await session.refresh(user)
    return user.score


async def add_correct(session: AsyncSession, vk_id: int) -> None:
    user = await get_or_create_user(session, vk_id)
    user.correct_answers += 1
    await session.commit()


async def get_correct_answers(session: AsyncSession, vk_id: int) -> int:
    user = await get_or_create_user(session, vk_id)
    await session.refresh(user)
    return user.correct_answers


async def log_action(session: AsyncSession, vk_id: int, action: str) -> None:
    user = await get_or_create_user(session, vk_id)
    session.add(History(user_id=user.id, action=action))
    await session.commit()