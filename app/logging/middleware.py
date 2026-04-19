import asyncio
import json
import logging
import time
import uuid

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import async_session
from app.logging.models import ApiLog

logger = logging.getLogger(__name__)

MODULE_NAME = "PROCUREMENT"
SKIP_PATHS = {"/procurement/health", "/procurement/docs", "/procurement/redoc", "/procurement/openapi.json", "/api/procurement/auth/login"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        query = request.url.query

        if path in SKIP_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        full_path = path + ("?" + query if query else "")
        client_ip = _extract_client_ip(request)
        user_id, user_role = _extract_jwt_claims(request)
        user_agent = request.headers.get("user-agent")
        request_body = await _read_request_body(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        response, response_body = await _capture_response_body(response)

        request_id = None
        if response_body and isinstance(response_body.get("responseId"), str):
            try:
                request_id = uuid.UUID(response_body["responseId"])
            except ValueError:
                pass

        asyncio.create_task(_persist_log(
            module=MODULE_NAME,
            request_id=request_id,
            method=request.method,
            path=full_path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            user_role=user_role,
            ip_address=client_ip,
            user_agent=user_agent,
            request_body=request_body,
            response_body=response_body,
        ))

        return response


def _extract_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def _extract_jwt_claims(request: Request) -> tuple[str | None, str | None]:
    """Extract (user_id, role) from the bearer token. Procurement currently puts
    an email in the `sub` claim — that gets stored in `user_id` until procurement
    migrates to the shared users table. The String(20) column accommodates both
    formats (e.g. 'admin@smart.com', 'ADM0000001')."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub"), payload.get("role")
    except (JWTError, Exception):
        return None, None


async def _read_request_body(request: Request) -> dict | None:
    if request.method in ("GET", "DELETE", "HEAD", "OPTIONS"):
        return None
    content_type = request.headers.get("content-type", "")
    if "multipart" in content_type or "application/json" not in content_type:
        return None
    try:
        body = await request.body()
        return json.loads(body)
    except Exception:
        return None


async def _capture_response_body(response: Response) -> tuple[Response, dict | None]:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response, None

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
    body_bytes = b"".join(chunks)

    try:
        body_dict = json.loads(body_bytes)
    except Exception:
        body_dict = None

    new_response = Response(
        content=body_bytes,
        status_code=response.status_code,
        headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
    )
    return new_response, body_dict


async def _persist_log(**kwargs) -> None:
    try:
        async with async_session() as session:
            session.add(ApiLog(**kwargs))
            await session.commit()
    except Exception as exc:
        logger.error("Failed to persist API log: %s", exc)
