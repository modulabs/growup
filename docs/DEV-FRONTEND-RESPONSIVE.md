# DEV - Frontend responsive/mobile optimization

## Goal

Make the current UI usable on mobile (responsive web).

Primary targets:
- Login
- Student course list + course detail (score tabs)
- Facilitator course list
- Facilitator course detail (quests + bonus sidebar + student list)
- Facilitator grading screen (quest scores)

Non-goals:
- Full redesign or new design system.
- Dark mode.

## Constraints

- Keep the existing visual language (Tailwind + current colors).
- Avoid breaking desktop workflows (especially grading keyboard flow).
- Prefer layout changes, not new routes.

## Breakpoints

Use standard Tailwind breakpoints:
- Base: mobile-first
- `sm` (>= 640px), `md` (>= 768px), `lg` (>= 1024px)

## Page-by-page plan

### 1) Global layout / navbar

Files:
- `frontend/src/routes/+layout.svelte`
- `frontend/src/lib/components/Navbar.svelte`

Changes:
- Reduce default padding on mobile: prefer `p-4 sm:p-6` across pages.
- Navbar: handle small widths
  - Stack user name + badge on very small screens
  - Ensure logout remains reachable (no overflow)

Acceptance:
- No horizontal scrolling on mobile for top-level layout.

### 2) Login page

File:
- `frontend/src/routes/login/+page.svelte`

Changes:
- Already largely mobile-friendly.
- Ensure input sizes are touch-friendly (min 44px tap targets).

Acceptance:
- Fits within viewport on iPhone SE-width without side scroll.

### 3) Student course detail (tables)

File:
- `frontend/src/routes/student/[courseId]/+page.svelte`

Pain points:
- Quest and bonus tables are wide; headers will overflow on small screens.

Changes:
- Wrap each table in `overflow-x-auto` container with `min-w-[...]` table width.
- Consider hiding non-critical columns on mobile using responsive utilities:
  - Example: hide "제목" / "날짜" columns below `sm`, or render them stacked.
- Ensure tabs are scrollable on mobile if needed (`overflow-x-auto`, `whitespace-nowrap`).

Acceptance:
- Mobile: tables scroll horizontally inside their container; page itself does not side-scroll.

### 4) Facilitator course detail (currently desktop-first)

File:
- `frontend/src/routes/facilitator/courses/[courseId]/+page.svelte`

Pain points:
- Two-column flex with a fixed-width sticky sidebar (`w-[380px]`) is not mobile friendly.

Changes:
- Switch to column layout on mobile:
  - `flex flex-col lg:flex-row`
  - Sidebar becomes full-width below `lg`
  - Sticky behavior only on desktop: `lg:sticky lg:top-6`
  - Explicit spacing between sections

Acceptance:
- Mobile: sections appear in a single vertical flow (quests -> bonus -> students) with no clipped content.

### 5) Facilitator grading screen (quest scores)

File:
- `frontend/src/routes/facilitator/quests/[questId]/+page.svelte`

Pain points:
- Score table has multiple columns; on mobile the table will be cramped.

Implementation options:

Option A (lowest risk): keep the table, add horizontal scroll.
- Wrap the table with `overflow-x-auto`.
- Ensure the action bar buttons wrap on small screens.

Option B (better UX, more work): mobile card view.
- Below `sm`, render each student as a card row:
  - Student name
  - Submitted toggle
  - Score input / pass-fail toggle
  - Status dot
- Above `sm`, render the existing table.

Recommended default: Option B if time allows; otherwise Option A.

Acceptance:
- Mobile: you can grade without zooming; touch targets are usable.
- Desktop: tab/keyboard flow still works.

## Verification checklist

- Pages tested at ~375px width and ~768px width.
- No global horizontal scrolling.
- Modals are usable on mobile (fit within viewport, scroll inside modal body if needed).
