from fastapi import APIRouter

from app.api.v1 import admin, auth, facilitator, student

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(admin.router, prefix="/admin")
api_router.include_router(student.router, prefix="/student")
api_router.include_router(facilitator.router, prefix="/facilitator")
