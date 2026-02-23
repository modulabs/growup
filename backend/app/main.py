from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.db.session import engine as async_engine



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on startup
    async with async_engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE cached_enrollments "
                "ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"
            )
        )
    yield


app = FastAPI(title="GrowUp API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "https://suncreation.github.io",
        "https://modulabs.github.io",
        "https://modulabs.ddns.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
