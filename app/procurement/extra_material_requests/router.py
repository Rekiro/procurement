from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.extra_material_requests import service
from app.procurement.extra_material_requests.schemas import (
    ExtraMaterialRequestCreate,
    ExtraMaterialRequestResponse,
    ApproveEMRRequest,
    RejectEMRRequest,
)

router = APIRouter()


@router.get("/status", response_model=ApiResponse)
async def get_emr_status(
    siteId: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    result = await service.get_status(db, user.sub, siteId)
    return success_response(result)


@router.post("", response_model=ApiResponse, status_code=201)
async def create_emr(
    data: ExtraMaterialRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emr = await service.create_request(db, data, user.sub)
    return success_response(ExtraMaterialRequestResponse.model_validate(emr).model_dump())


@router.get("", response_model=ApiResponse)
async def list_emrs(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emrs = await service.list_requests(db, status_filter=status)
    return success_response([ExtraMaterialRequestResponse.model_validate(e).model_dump() for e in emrs])


@router.post("/approve", response_model=ApiResponse)
async def approve_emr(
    data: ApproveEMRRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emr = await service.approve_request(db, data, approved_by=user.sub)
    return success_response(ExtraMaterialRequestResponse.model_validate(emr).model_dump())


@router.post("/{request_id}/reject", response_model=ApiResponse)
async def reject_emr(
    request_id: str,
    data: RejectEMRRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emr = await service.reject_request(db, request_id, data, reviewed_by=user.sub)
    return success_response(ExtraMaterialRequestResponse.model_validate(emr).model_dump())
