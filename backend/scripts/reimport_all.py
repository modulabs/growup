import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.db.session import async_session
from app.services.sheet_service import import_from_sheet

COURSES = [
    (2, "1BKPnRPbmzoufvg7P0aqDN0nErMnQfKMq1spElKzFsDM"),
    (3, "1G-w3d1grs-PHsOb7zhxgKiigOSxL1Tey4XD4BAap20g"),
    (4, "19uVyaOJiO0Gyl3r6Z954md2Bs4HEbuyC7BnRbTsDTs4"),
    (10, "1BpVUJ_UTqqE6PI4nu4iN_VQPaeF8sPIH1-DJ9PzhGmI"),
    (11, "1abDR3kSIqwZcxHe90QN_rTAQqUbLL0BGHvPyNp02e4k"),
    (12, "1quWGSAcpaxR-0GHYfJSTMq3gIN4zLv2-rYxfMb6FtCc"),
    (13, "129SyAU7YCTZpzpT0D7zGuWMN2e0cADFCuoFPlA_Uj60"),
    (14, "1jCso2KY1OkL7YouKPNpaUXNiK9Kpxdy-YGeEbZZOuf4"),
    (15, "14sGkbzQnvrwFEkTAK-GTpx4KbWxmq8d6g5Y2vJs35uw"),
]


async def main():
    facilitator_id = 29859
    async with async_session() as db:
        for course_id, sheet_id in COURSES:
            print(f"\nImporting Course {course_id}...")
            try:
                result = await import_from_sheet(
                    db, sheet_id, course_id, facilitator_id, sheet_name="퀘스트"
                )
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error importing course {course_id}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
