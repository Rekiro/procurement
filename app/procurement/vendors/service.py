import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.vendors.models import ProcVendor, ProcVendorApplication
from app.procurement.vendors.schemas import (
    VendorCreate, VendorApplicationData,
    ApproveApplicationRequest, RejectApplicationRequest,
)
from app.shared.pagination import paginate


async def create_vendor(db: AsyncSession, data: VendorCreate) -> ProcVendor:
    existing = await db.scalar(select(ProcVendor).where(ProcVendor.email == data.emailId))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "A vendor with this email already exists",
                "vendorCode": existing.vendor_code,
            },
        )

    count = await db.scalar(select(func.count()).select_from(ProcVendor))
    vendor_code = f"VEN{(count or 0) + 1:07d}"
    invite_token = secrets.token_urlsafe(32)

    vendor = ProcVendor(
        vendor_code=vendor_code,
        company_name=data.vendorName,
        email=data.emailId,
        state=data.state,
        nature_of_business=data.natureOfBusiness,
        status="INVITED",
        invite_token=invite_token,
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


async def get_vendor_by_email(db: AsyncSession, email: str) -> ProcVendor:
    vendor = await db.scalar(select(ProcVendor).where(ProcVendor.email == email))
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vendor record found for this email. Contact procurement head.")
    return vendor


async def create_vendor_application(
    db: AsyncSession,
    vendor_code: str,
    data: VendorApplicationData,
    file_urls: dict[str, str],
    gst_cert_urls: dict[str, str],
) -> ProcVendorApplication:
    existing_app = await db.scalar(
        select(ProcVendorApplication)
        .where(ProcVendorApplication.vendor_code == vendor_code)
        .where(ProcVendorApplication.status == "Pending")
    )
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"A pending application already exists for vendor {vendor_code}",
                "vendorCode": vendor_code,
            },
        )

    # Build gstDetails with URLs for storage
    gst_details_with_urls = []
    for gst in data.gstDetails:
        entry = {
            "state": gst.state,
            "gstNumber": gst.gstNumber,
            "gstCertificateUrl": gst_cert_urls.get(gst.gstCertificate, ""),
        }
        gst_details_with_urls.append(entry)

    application = ProcVendorApplication(
        vendor_code=vendor_code,
        name=data.name,
        name_of_owner=data.nameOfOwner,
        email=data.email,
        designation=data.designation,
        category=data.category,
        types_of_business=data.typesOfBusiness,
        address_line1=data.addressLine1,
        address_line2=data.addressLine2,
        state=data.state,
        district=data.district,
        city=data.city,
        pin_code=data.pinCode,
        gst_details=gst_details_with_urls,
        shop_establishment_url=file_urls.get("shopAndEstablishmentNo"),
        pan_url=file_urls.get("panNo"),
        aadhaar_udyam_url=file_urls.get("aadhaarOrUdyamCopy"),
        msme_certificate_url=file_urls.get("msmeCertificate"),
        cancelled_cheque_url=file_urls.get("cancelledCheque"),
        escalation_matrix_url=file_urls.get("escalationMatrix"),
        branch_office_details_url=file_urls.get("branchOfficeDetails"),
        board_resolution_url=file_urls.get("boardResolution"),
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def list_vendor_applications(
    db: AsyncSession,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[ProcVendorApplication], dict]:
    q = select(ProcVendorApplication).order_by(ProcVendorApplication.submitted_at.desc())
    if status_filter:
        q = q.where(ProcVendorApplication.status == status_filter)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                ProcVendorApplication.name.ilike(term),
                ProcVendorApplication.category.ilike(term),
                ProcVendorApplication.email.ilike(term),
            )
        )
    return await paginate(q, db, page=page, limit=limit)


async def get_vendor_application(db: AsyncSession, vendor_code: str) -> ProcVendorApplication:
    result = await db.execute(
        select(ProcVendorApplication).where(ProcVendorApplication.vendor_code == vendor_code)
        .order_by(ProcVendorApplication.submitted_at.desc())
    )
    application = result.scalars().first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


async def approve_vendor_applications(
    db: AsyncSession,
    data: ApproveApplicationRequest,
    reviewed_by: str,
) -> list[ProcVendorApplication]:
    approved = []
    for vc in data.vendorIds:
        application = await db.scalar(
            select(ProcVendorApplication)
            .where(ProcVendorApplication.vendor_code == vc)
            .where(ProcVendorApplication.status == "Pending")
        )
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pending application not found for vendor {vc}",
            )

        vendor = await db.get(ProcVendor, vc)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor record not found for {vc}")

        approved_count = await db.scalar(
            select(func.count()).select_from(ProcVendor).where(ProcVendor.status == "ACTIVE")
        )
        gl_code = f"GL{datetime.now(timezone.utc).year}{(approved_count or 0) + 1:07d}"

        vendor.status = "ACTIVE"
        vendor.gl_code = gl_code
        vendor.invite_token = None

        application.status = "Approved"
        application.reviewed_at = datetime.now(timezone.utc)
        application.reviewed_by = reviewed_by

        approved.append(application)

    await db.commit()
    for app in approved:
        await db.refresh(app)
    return approved


async def reject_vendor_application(db: AsyncSession, vendor_code: str, data: RejectApplicationRequest, reviewed_by: str) -> ProcVendorApplication:
    application = await db.scalar(
        select(ProcVendorApplication)
        .where(ProcVendorApplication.vendor_code == vendor_code)
        .where(ProcVendorApplication.status == "Pending")
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending application not found")

    application.status = "Rejected"
    application.rejection_reason = data.reason
    application.reviewed_at = datetime.now(timezone.utc)
    application.reviewed_by = reviewed_by

    await db.commit()
    await db.refresh(application)
    return application
