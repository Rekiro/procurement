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
    requestorEmail: str = Query("admin@smart.com"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    result = await service.get_status(db, requestorEmail, siteId)
    return success_response(result)


@router.post("", response_model=ApiResponse, status_code=201)
async def create_emr(
    data: ExtraMaterialRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emr = await service.create_request(db, data)
    return success_response(ExtraMaterialRequestResponse.from_orm(emr).model_dump())


@router.get("", response_model=ApiResponse)
async def list_emrs(
    status: str = Query(..., description="Filter by status, e.g. 'pending'"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    requests_list, pagination = await service.list_requests_paginated(
        db, status_filter=status, page=page, limit=limit
    )
    return success_response({"pagination": pagination, "requests": requests_list})


@router.post("/approve", response_model=ApiResponse)
async def approve_emr(
    data: ApproveEMRRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emrs = await service.approve_requests(db, data.emrIds, approved_by=user.sub)
    return success_response([ExtraMaterialRequestResponse.from_orm(e).model_dump() for e in emrs])


@router.post("/{request_id}/reject", response_model=ApiResponse)
async def reject_emr(
    request_id: str,
    data: RejectEMRRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    emr = await service.reject_request(db, request_id, data, reviewed_by=user.sub)
    return success_response(ExtraMaterialRequestResponse.from_orm(emr).model_dump())
