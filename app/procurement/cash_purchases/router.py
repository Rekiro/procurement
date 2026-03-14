import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.cash_purchases import service
from app.procurement.cash_purchases.schemas import (
    CashPurchaseCreate, CashPurchaseResponse,
    ApproveCashPurchaseRequest, RejectCashPurchaseRequest,
)

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def create_cash_purchase(
    data: CashPurchaseCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    purchase = await service.create_cash_purchase(db, data, user.sub)
    return success_response(CashPurchaseResponse.from_orm(purchase).model_dump())


@router.get("", response_model=ApiResponse)
async def list_cash_purchases(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    purchases = await service.list_cash_purchases(db, status_filter=status)
    return success_response([CashPurchaseResponse.from_orm(p).model_dump() for p in purchases])


@router.post("/approve", response_model=ApiResponse)
async def approve_cash_purchase(
    data: ApproveCashPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    purchase = await service.approve_cash_purchase(db, data, reviewed_by=user.sub)
    return success_response(CashPurchaseResponse.from_orm(purchase).model_dump())


@router.post("/{purchase_id}/reject", response_model=ApiResponse)
async def reject_cash_purchase(
    purchase_id: uuid.UUID,
    data: RejectCashPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    purchase = await service.reject_cash_purchase(db, purchase_id, data, reviewed_by=user.sub)
    return success_response(CashPurchaseResponse.from_orm(purchase).model_dump())
