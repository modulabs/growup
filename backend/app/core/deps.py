from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.session import get_db  # noqa: F401 — re-export

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return payload


async def require_facilitator(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "facilitator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Facilitator access required"
        )
    return current_user


async def require_student(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student access required"
        )
    return current_user
