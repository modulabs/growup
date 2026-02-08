import asyncio
import sys
import os

sys.path.append(os.getcwd())
from app.services.legacy_service import get_rubric_scores_for_student, _query_legacy


async def main():
    # 1. Find correct Lee Gyucheol in Group 1
    ids = [34976, 32897, 65771]
    ids_str = ", ".join(map(str, ids))

    sql_check = f"""
    SELECT user_id 
    FROM user_group_mapping 
    WHERE user_group_id = 1 
      AND user_id IN ({ids_str})
    """
    print("Checking which Lee Gyucheol is in Group 1...")
    try:
        rows = await _query_legacy(sql_check)
        print(f"Group 1 Members: {rows}")
        if not rows:
            print("No Lee Gyucheol found in Group 1")
            return
        uid = rows[0]["user_id"]
    except Exception as e:
        print(f"Error checking group: {e}")
        return

    print(f"Target User ID: {uid}")

    # 2. Test Rubric Query (Optimized) with LIMIT
    # Use the logic from legacy_service directly to debug
    sql_courses = (
        "SELECT course_id FROM user_group_course_mapping WHERE user_group_id = 1"
    )
    courses = await _query_legacy(sql_courses)
    course_ids = [str(c["course_id"]) for c in courses]
    course_ids_str = ", ".join(course_ids)
    print(f"Courses in Group 1: {len(course_ids)}")

    # Minimal query
    sql_minimal = f"""
    SELECT count(*)
    FROM core_evaluation e
    JOIN core_nodeprogrs np ON e.node_progrs_id = np.id
    JOIN core_userenrolments ue ON np.user_enrolments_id = ue.id
    WHERE ue.user_id = {uid}
      AND ue.course_id IN ({course_ids_str})
    """
    print("Running minimal count query...")
    try:
        res = await _query_legacy(sql_minimal)
        print(f"Count: {res}")
    except Exception as e:
        print(f"Minimal query failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
