import asyncio
import sys

# Windows + Python < 3.14: psycopg async requires SelectorEventLoop
if sys.platform == "win32" and sys.version_info < (3, 14):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.logging.middleware import RequestLoggingMiddleware
from app.shared.schemas import ApiErrorResponse, ErrorDetail

from app.auth.router import router as auth_router
from app.procurement.vendors.router import router as vendors_router, applications_router as vendor_applications_router
from app.procurement.products.router import router as products_router, vendor_router as vendor_products_router
from app.procurement.sites.router import router as sites_router
from app.procurement.extra_material_requests.router import router as emr_router
from app.procurement.indents.router import router as indents_router
from app.procurement.purchase_orders.router import router as po_router
from app.procurement.invoices.router import router as invoices_router
from app.procurement.cash_purchases.router import router as cash_router
from app.procurement.machinery_requests.router import router as machinery_router
from app.procurement.uniform_requests.router import router as uniform_router
from app.procurement.notifications.router import router as notifications_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/procurement/docs",
    redoc_url="/procurement/redoc",
    openapi_url="/procurement/openapi.json",
)

app.add_middleware(RequestLoggingMiddleware)

_STATUS_TO_ERROR_TYPE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_type = _STATUS_TO_ERROR_TYPE.get(exc.status_code, "INTERNAL_SERVER_ERROR")
    if isinstance(exc.detail, dict):
        # Extract known keys; pass everything else as extra fields on ErrorDetail
        extra = {k: v for k, v in exc.detail.items() if k not in ("message", "errors")}
        errors = [
            ErrorDetail(
                errorType=error_type,
                errorMessage=exc.detail.get("message", str(exc.detail)),
                location="",
                **extra,
            )
        ]
        for inner_err in exc.detail.get("errors", []):
            errors.append(ErrorDetail(errorType="VALIDATION_ERROR", errorMessage=str(inner_err), location=""))
    else:
        errors = [ErrorDetail(errorType=error_type, errorMessage=str(exc.detail), location="")]
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(errors=errors).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        ErrorDetail(
            errorType="VALIDATION_ERROR",
            errorMessage=err["msg"],
            location=".".join(str(loc) for loc in err["loc"]),
        )
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ApiErrorResponse(errors=errors).model_dump(),
    )


# Auth
app.include_router(auth_router, prefix="/api/procurement/auth", tags=["Auth"])

# Vendors
app.include_router(vendors_router, prefix="/api/procurement/vendors", tags=["Vendors"])
app.include_router(vendor_applications_router, prefix="/api/procurement/vendor-applications", tags=["Vendor Applications"])

# Products
app.include_router(products_router, prefix="/api/procurement/products", tags=["Products"])
app.include_router(vendor_products_router, prefix="/api/procurement", tags=["Products"])

# Sites (routes defined with full sub-paths, e.g. /user-sites, /sites/{id}/...)
app.include_router(sites_router, prefix="/api/procurement", tags=["Sites"])

# Extra Material Requests
app.include_router(emr_router, prefix="/api/procurement/extra-material-requests", tags=["Extra Material Requests"])

# Indents
app.include_router(indents_router, prefix="/api/procurement/indents", tags=["Indents"])

# Purchase Orders
app.include_router(po_router, prefix="/api/procurement/purchase-orders", tags=["Purchase Orders"])

# Invoices
app.include_router(invoices_router, prefix="/api/procurement/invoices", tags=["Invoices"])

# Cash Purchases
app.include_router(cash_router, prefix="/api/procurement/cash-purchases", tags=["Cash Purchases"])

# Machinery
app.include_router(machinery_router, prefix="/api/procurement", tags=["Machinery"])

# Uniforms
app.include_router(uniform_router, prefix="/api/procurement", tags=["Uniforms"])

# Notifications
app.include_router(notifications_router, prefix="/api/procurement/notifications", tags=["Notifications"])


@app.get("/procurement/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
