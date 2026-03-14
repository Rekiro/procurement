import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.notifications.models import ProcNotification


async def list_notifications(db: AsyncSession, user_email: str) -> list[ProcNotification]:
    result = await db.execute(
        select(ProcNotification)
        .where(ProcNotification.user_email == user_email)
        .order_by(ProcNotification.created_at.desc())
    )
    return list(result.scalars().all())


async def mark_as_read(db: AsyncSession, ids: list[uuid.UUID], user_email: str) -> int:
    result = await db.execute(
        update(ProcNotification)
        .where(
            ProcNotification.id.in_(ids),
            ProcNotification.user_email == user_email,
        )
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount


async def create_notification(
    db: AsyncSession,
    user_email: str,
    title: str,
    message: str,
    link: str | None = None,
) -> ProcNotification:
    notif = ProcNotification(
        user_email=user_email,
        title=title,
        message=message,
        link=link,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif
