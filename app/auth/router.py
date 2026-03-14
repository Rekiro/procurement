from fastapi import APIRouter, HTTPException, status

from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.dependencies import create_access_token
from app.shared.schemas import ApiResponse, success_response

router = APIRouter()

# Single credential for now — extend this dict when client specifies consumers
_USERS = {
    "admin@smart.com": ("admin", "admin"),
}


@router.post("/login", response_model=ApiResponse)
async def login(request: LoginRequest):
    entry = _USERS.get(request.email)
    if entry and entry[0] == request.password:
        token = create_access_token({"sub": request.email, "role": entry[1]})
        return success_response(TokenResponse(access_token=token).model_dump())
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )
