from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.notifications import service
from app.procurement.notifications.schemas import NotificationResponse, MarkAsReadRequest

router = APIRouter()


@router.get("", response_model=ApiResponse)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    notifs = await service.list_notifications(db, user.sub)
    return success_response([NotificationResponse.model_validate(n).model_dump() for n in notifs])


@router.post("/mark-as-read", response_model=ApiResponse)
async def mark_as_read(
    data: MarkAsReadRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    count = await service.mark_as_read(db, data.ids, user.sub)
    return success_response({"marked": count})
