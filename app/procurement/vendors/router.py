import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.shared.file_storage import upload_fastapi_file
from app.procurement.vendors import service
from app.procurement.vendors.schemas import (
    VendorCreate, VendorResponse, VendorApplicationData,
    VendorApplicationListItem, VendorApplicationResponse,
    ApproveApplicationRequest, RejectApplicationRequest,
)

# Registered at /api/procurement/vendors
router = APIRouter()

# Registered at /api/procurement/vendor-applications
applications_router = APIRouter()

# File field names expected in multipart vendor application
_FIXED_FILE_FIELDS = [
    "shopAndEstablishmentNo",
    "panNo",
    "aadhaarOrUdyamCopy",
    "msmeCertificate",
    "cancelledCheque",
    "escalationMatrix",
    "branchOfficeDetails",
    "boardResolution",
]


# --- Vendor CRUD ---

@router.post("", response_model=ApiResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    vendor = await service.create_vendor(db, data)
    return success_response(VendorResponse.from_orm(vendor).model_dump())


# --- Vendor Applications ---

@applications_router.post("", response_model=ApiResponse, status_code=201)
async def submit_vendor_application(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    # Parse multipart/form-data
    form = await request.form()

    # 1. Parse the 'data' JSON field
    raw_data = form.get("data")
    if not raw_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'data' field in form")
    try:
        data_dict = json.loads(raw_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'data' field is not valid JSON")

    try:
        data = VendorApplicationData(**data_dict)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # 2. Look up vendor by the email in the form data (not JWT email,
    #    since a single admin credential submits on behalf of vendors)
    vendor = await service.get_vendor_by_email(db, data.email)
    prefix = f"vendor-applications/{vendor.vendor_code}"

    # 3. Validate boardResolution requirement
    requires_board_resolution = data.typesOfBusiness in ("Private Limited", "LLP")
    if requires_board_resolution and "boardResolution" not in form:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="boardResolution file is required when typesOfBusiness is 'Private Limited' or 'LLP'",
        )

    # 4. Upload fixed file fields — named by document type, not UUID
    file_urls: dict[str, str] = {}
    for field_name in _FIXED_FILE_FIELDS:
        file = form.get(field_name)
        if file is None:
            if field_name == "boardResolution" and not requires_board_resolution:
                continue
            if field_name != "boardResolution":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required file: {field_name}",
                )
            continue
        # Use document type as filename: vendor-applications/VEN0001/panNo.pdf
        ext_map = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
        ext = ext_map.get(file.content_type, "bin")
        object_name = f"{prefix}/{field_name}.{ext}"
        file_urls[field_name] = await upload_fastapi_file(file, object_name=object_name)

    # 5. Upload GST certificate files — named by index
    gst_cert_urls: dict[str, str] = {}
    for i, gst in enumerate(data.gstDetails):
        cert_field = gst.gstCertificate
        cert_file = form.get(cert_field)
        if cert_file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing GST certificate file: {cert_field}",
            )
        ext_map = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
        ext = ext_map.get(cert_file.content_type, "bin")
        object_name = f"{prefix}/gstCertificate-{i}.{ext}"
        gst_cert_urls[cert_field] = await upload_fastapi_file(cert_file, object_name=object_name)

    application = await service.create_vendor_application(
        db, vendor.vendor_code, data, file_urls=file_urls, gst_cert_urls=gst_cert_urls,
    )
    return success_response(VendorApplicationResponse.from_orm(application).model_dump())


@applications_router.get("", response_model=ApiResponse)
async def list_vendor_applications(
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    applications, pagination = await service.list_vendor_applications(
        db, status_filter=status, search=search, page=page, limit=limit,
    )
    return success_response({
        "pagination": pagination,
        "vendors": [VendorApplicationListItem.from_orm(a).model_dump() for a in applications],
    })


@applications_router.post("/approve", response_model=ApiResponse)
async def approve_vendor_applications(
    data: ApproveApplicationRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    applications = await service.approve_vendor_applications(db, data, reviewed_by=user.sub)
    return success_response([VendorApplicationResponse.from_orm(a).model_dump() for a in applications])


@applications_router.get("/{vendor_code}", response_model=ApiResponse)
async def get_vendor_application(
    vendor_code: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    application = await service.get_vendor_application(db, vendor_code)
    return success_response(VendorApplicationResponse.from_orm(application).model_dump())


@applications_router.post("/{vendor_code}/reject", response_model=ApiResponse)
async def reject_vendor_application(
    vendor_code: str,
    data: RejectApplicationRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    application = await service.reject_vendor_application(db, vendor_code, data, reviewed_by=user.sub)
    return success_response(VendorApplicationResponse.from_orm(application).model_dump())
