# DEV - Login switch to email + phone

## Goal

Replace the current login method (name + phone) with **email + phone**.

Rationale:
- Name collisions are common and make impersonation easier.
- Email is typically unique and already exists in the legacy system.

Non-goals:
- Introducing a full signup/registration flow.
- Changing role rules (student vs facilitator) beyond what the current backend already does.

## Current State (as-is)

- Backend login endpoint: `POST /api/v1/auth/login`
  - Request: `name`, `phone` (`backend/app/schemas/auth.py`)
  - Legacy lookup: `core_user.first_name` + `core_userprivacy.phone_number` (`backend/app/services/legacy_service.py#verify_user`)
  - JWT payload includes: `legacy_user_id`, `name`, `role` (`backend/app/services/auth_service.py`)

- Frontend login page: `frontend/src/routes/login/+page.svelte`
  - Inputs: name + phone
  - Sends: `{ name, phone }` to `/api/v1/auth/login`

## Legacy DB: confirm the email field

We must confirm where the legacy email is stored before changing the SQL.

### Step 1) Find candidate columns

Run one of these through the legacy query mechanism (n8n webhook / admin query tool):

```sql
-- Find email-like columns in core_user
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'core_user'
  AND column_name ILIKE '%mail%'
ORDER BY column_name;

-- Find email-like columns in core_userprivacy
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'core_userprivacy'
  AND column_name ILIKE '%mail%'
ORDER BY column_name;
```

### Step 2) Confirm a real value exists

Once you have the field name, validate it contains values:

```sql
SELECT cu.id, cu.first_name, cup.phone_number,
       /* replace with the discovered email field */
       cu.email
FROM core_user cu
JOIN core_userprivacy cup ON cu.id = cup.user_id
WHERE cu.id IS NOT NULL
ORDER BY cu.id DESC
LIMIT 5;
```

### Expected outcome

Decide and document a single canonical source, for example:
- Option A (recommended if present): `core_user.email`
- Option B: `core_user.username` (if it is an email in this system)
- Option C: `core_userprivacy.email`

If there is no usable email field, stop and revisit the approach (do not guess).

## API contract change

### Endpoint

`POST /api/v1/auth/login`

### Request

- New: `{ "email": string, "phone": string }`
- Old: `{ "name": string, "phone": string }` is removed unless we explicitly keep backward compatibility.

Compatibility decision:
- Default for this task: **break intentionally** (frontend will be updated in the same change).
- If backward compatibility is required later, accept both payload shapes and prioritize `email+phone`.

### Response

Keep the existing response shape:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "legacy_user_id": 123,
  "name": "홍길동",
  "role": "student | facilitator",
  "active_courses": [{ "legacy_course_id": 15, "name": "AI 리서처 16기" }]
}
```

Note: even with email login, the UI still wants a human name. Continue to read `first_name` from legacy and return `name`.

## Backend implementation plan

### 1) Schema update

- `backend/app/schemas/auth.py`
  - `LoginRequest`: replace `name: str` with `email: str`

### 2) Legacy lookup function

- `backend/app/services/legacy_service.py`
  - Replace `verify_user(name, phone)` with `verify_user(email, phone)` (or create a new function and update callers)
  - Update the SQL to filter by `email` and `phone_number`

Important: current code uses f-strings to embed user input into SQL.
- At minimum, escape single quotes in user-provided fields.
- Prefer a small helper like `sql_literal(value: str) -> str` that returns a safely-quoted literal.
- Do not log raw phone/email in server logs.

### 3) Auth service

- `backend/app/services/auth_service.py`
  - Update `login()` signature and call into `legacy_service.verify_user(email, phone)`
  - Keep role resolution behavior unchanged

### 4) Frontend client expectations

No backend changes needed besides request schema and legacy lookup.

## Frontend implementation plan

### 1) Login page UI + request

- `frontend/src/routes/login/+page.svelte`
  - Replace the name input with an email input
  - Send `{ email, phone }` to `/api/v1/auth/login`
  - Keep the same error UX

### 2) Types

- `frontend/src/lib/types/index.ts`
  - Update `LoginResponse` request typing if you model request bodies
  - No changes required to `LoginResponse` itself

## Test / Verification checklist

Backend:
- `POST /api/v1/auth/login` with valid `email+phone` returns 200 and a JWT.
- Invalid combo returns 401 with existing user-friendly message behavior preserved on the frontend.

Frontend:
- Login success routes correctly based on role.

Suggested commands:

```bash
# Backend (syntax / import)
python -m compileall backend/app

# Frontend (typecheck + build)
cd frontend
npm run check
npm run build
```
