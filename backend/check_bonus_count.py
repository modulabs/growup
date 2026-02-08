import asyncio
import sys
import os

sys.path.append(os.getcwd())
from app.db.session import async_session
from sqlalchemy import text


async def main():
    async with async_session() as db:
        res = await db.execute(text("SELECT count(*) FROM bonus_scores"))
        print(f"Total Bonus Scores: {res.scalar()}")


if __name__ == "__main__":
    asyncio.run(main())
