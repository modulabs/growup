import asyncio
import sys
import os

sys.path.append(os.getcwd())
from app.db.session import async_session
from sqlalchemy import select
from app.models.cache import CachedUser, CachedEnrollment


async def main():
    async with async_session() as db:
        stmt = (
            select(CachedUser.name)
            .join(
                CachedEnrollment,
                CachedUser.legacy_user_id == CachedEnrollment.legacy_user_id,
            )
            .where(CachedEnrollment.legacy_course_id == 15)
        )
        rows = (await db.execute(stmt)).scalars().all()
        print(f"Users in DB for Course 15 ({len(rows)}): {rows}")


if __name__ == "__main__":
    asyncio.run(main())
