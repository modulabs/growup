import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"


def login():
    # Lee Gyucheol
    phone = "01090285030"
    resp = requests.post(
        f"{BASE_URL}/auth/login", json={"name": "이규철", "phone": phone}
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return None
    return resp.json()


def get_scores(token, course_id):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/student/courses/{course_id}/scores"
    print(f"GET {url}")
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        bonuses = data.get("bonus_scores", [])
        print(f"Bonus Scores: {len(bonuses)}")
        for b in bonuses:
            print(f"Reason: {b['reason']}, Giver: {b['given_by_name']}")
    else:
        print(resp.text)


if __name__ == "__main__":
    auth = login()
    if auth:
        token = auth["access_token"]
        get_scores(token, 1)
