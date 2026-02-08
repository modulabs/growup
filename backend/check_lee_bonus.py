import asyncio
import sys
import os

sys.path.append(os.getcwd())
from app.db.session import async_session
from sqlalchemy import text


async def main():
    uid = 32897
    async with async_session() as db:
        res = await db.execute(
            text(f"SELECT * FROM bonus_scores WHERE legacy_student_id = {uid}")
        )
        rows = res.fetchall()
        print(f"Bonus Scores for {uid}: {len(rows)}")
        for r in rows:
            print(r)


if __name__ == "__main__":
    asyncio.run(main())
