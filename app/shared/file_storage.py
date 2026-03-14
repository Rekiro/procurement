import uuid as _uuid
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from minio import Minio

from app.config import settings

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
    return _client


def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.put_object(
        settings.minio_bucket,
        object_name,
        BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return f"{settings.minio_bucket}/{object_name}"


async def upload_fastapi_file(file: UploadFile, prefix: str = "", object_name: str = "") -> str:
    """Validate and upload a FastAPI UploadFile to MinIO.

    Pass object_name for a human-readable path (e.g. "vendor-applications/VEN0001/panNo.pdf").
    Pass prefix for auto-generated UUID-based names (e.g. "uploads/invoices").
    Returns the stored object path (bucket/object_name).
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}': type '{file.content_type}' not allowed. "
                   f"Allowed: PDF, JPEG, PNG.",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' exceeds 1 MB limit.",
        )

    if not object_name:
        ext_map = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
        ext = ext_map.get(file.content_type, "bin")
        object_name = f"{prefix}/{_uuid.uuid4()}.{ext}"
    return upload_file(object_name, data, file.content_type)


def download_file(object_name: str) -> bytes:
    client = get_minio_client()
    response = client.get_object(settings.minio_bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
