from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.auth.dependencies import get_current_user
from app.shared.file_storage import download_file
from app.config import settings

router = APIRouter()

_EXT_TO_CONTENT_TYPE = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


@router.get("/preview")
async def preview_file(
    path: str = Query(..., min_length=1, description="File path as stored in DB (with or without bucket prefix)"),
    download: bool = Query(False, description="Set to true to force download instead of inline preview"),
    _user: dict = Depends(get_current_user),
):
    # Strip bucket prefix if present (DB stores "smarterp-procurement/vendor-apps/...", MinIO expects "vendor-apps/...")
    bucket_prefix = f"{settings.minio_bucket}/"
    object_name = path[len(bucket_prefix):] if path.startswith(bucket_prefix) else path

    ext = object_name.rsplit(".", 1)[-1].lower() if "." in object_name else ""
    content_type = _EXT_TO_CONTENT_TYPE.get(ext, "application/octet-stream")

    try:
        data = download_file(object_name)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}")

    filename = object_name.rsplit("/", 1)[-1] if "/" in object_name else object_name
    disposition = "attachment" if download else "inline"

    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )
