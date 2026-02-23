# GrowUp - Ralph Loop Prompt: Email+Phone Login + Mobile Responsive

## Instructions

You will implement two changes:

1) Switch login from (name + phone) to **(email + phone)**.
2) Make the frontend responsive for mobile usage.

### Read these docs first

1. `docs/DEV-AUTH-EMAIL-PHONE.md`
2. `docs/DEV-FRONTEND-RESPONSIVE.md`
3. `docs/PRD-backend.md`
4. `docs/PRD-frontend.md`

## Hard constraints

- Legacy DB runtime access must stay via n8n webhook (HTTP). No direct DB connection.
- Do not add new dependencies unless strictly necessary.
- Do not change role logic (student/facilitator) except what is required by the auth input change.
- Keep changes focused: do not refactor unrelated areas.

## Current state (starting point)

- Backend login is `POST /api/v1/auth/login` and currently uses `name + phone`.
- Frontend login UI uses `name + phone`.
- Several pages are desktop-first and overflow on mobile.

## End state (must all be true)

### A) Auth

- Backend:
  - `POST /api/v1/auth/login` accepts `{ email, phone }`.
  - Legacy lookup uses the canonical legacy email field (must be confirmed via schema introspection query first).
  - Successful login returns the existing `LoginResponse` shape with `name` populated.
  - Invalid credentials return 401.

- Frontend:
  - Login form uses email + phone.
  - Successful login continues to route users by role (student -> `/student`, facilitator -> `/facilitator`).

### B) Mobile responsive

- On mobile widths (~375px):
  - No global horizontal scroll.
  - Student score views and facilitator views remain readable.
  - Facilitator course detail page is a single-column flow; sidebar sections do not overflow.
  - Grading screen is usable (either horizontal-scroll table, or mobile card view).

## Implementation checklist

1) Confirm legacy email field
- Use SQL introspection queries from `docs/DEV-AUTH-EMAIL-PHONE.md`.
- Do not guess the email column name.

2) Update backend auth
- Update `backend/app/schemas/auth.py`.
- Update legacy query in `backend/app/services/legacy_service.py`.
- Update `backend/app/services/auth_service.py`.
- Update any references in frontend typings if needed.

3) Update frontend login
- Update `frontend/src/routes/login/+page.svelte`.
- Preserve existing error messaging UX.

4) Responsive work
- Apply changes in `docs/DEV-FRONTEND-RESPONSIVE.md`.
- Ensure modals and tables do not break mobile layout.

## Verification

Run these commands and fix failures introduced by your changes:

```bash
python -m compileall backend/app

cd frontend
npm run check
npm run build
```

## Notes

- If you discover a backend/frontend contract mismatch while implementing these tasks, only fix it if it blocks these end-state requirements.
