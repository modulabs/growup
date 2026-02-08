"""Seed script: Register facilitator overrides.

Usage:
    cd backend
    python -m scripts.seed_facilitator_override

This inserts manual facilitator overrides for users who are not
marked as COACH in the Legacy DB but should have facilitator access.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.models.override import FacilitatorOverride

# ── Override entries to seed ──
OVERRIDES = [
    {
        "legacy_user_id": 29859,  # 조해창 (phone: 01029334511)
        "name": "조해창",
        "phone": "01029334511",
        "reason": "퍼실리테이터 수동 등록 (요청)",
    },
]


async def seed() -> None:
    async with async_session() as db:
        db: AsyncSession
        for entry in OVERRIDES:
            existing = await db.execute(
                select(FacilitatorOverride).where(
                    FacilitatorOverride.legacy_user_id == entry["legacy_user_id"]
                )
            )
            if existing.scalar_one_or_none():
                print(f"  SKIP: {entry['name']} (already exists)")
                continue

            override = FacilitatorOverride(**entry)
            db.add(override)
            print(f"  ADD:  {entry['name']} (legacy_user_id={entry['legacy_user_id']})")

        await db.commit()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
