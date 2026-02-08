import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.db.session import async_session
from app.services.cache_service import sync_students_for_course
from app.services.sheet_service import import_from_sheet


async def main():
    course_id = 15
    sheet_id = "1DSlJEsdqUSZIoXXvNImoEEaSmsucaHLjoVI_1rMaC9g"
    facilitator_id = 29859

    async with async_session() as db:
        print(f"Syncing students for Course {course_id}...")
        try:
            users = await sync_students_for_course(db, course_id)
            print(f"Synced {len(users)} students.")
        except Exception as e:
            print(f"Sync failed: {e}")

        print(f"Importing from Sheet {sheet_id}...")
        result = await import_from_sheet(
            db, sheet_id, course_id, facilitator_id, sheet_name="퀘스트"
        )
        print(f"Import Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
