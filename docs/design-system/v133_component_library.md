# v133 Component Library

v133 adds the shared component catalog for the UX redesign block. The goal is to give admin, trainer, student and public screens one stable frontend vocabulary before the screen-by-screen redesign begins.

## Scope

Component library file:

- `frontend/src/design-system/library.tsx`

Global styles:

- `frontend/src/app/globals.css`

Contract coverage:

- `frontend/tests/contracts/design-system-contract.test.js`

## Components

The v133 library covers:

- `DSDataTable` for admin and operations tables.
- `DSBarChart` for compact business metrics.
- `DSCalendar` for booking, schedule and subscription lifecycle views.
- `DSKanbanBoard` for CRM, support and workflow states.
- `DSFileUpload` for media, finance documents and trainer materials.
- `DSRichTextEditor` shell for course content, notes and support replies.
- `DSVideoPlayer` for protected learning content UI.
- `DSStatsGrid` and `DSStatCard` for dashboard KPI blocks.
- `DSComponentPreview` for internal design-system examples.

## Rules

- Components are presentational and do not own business logic.
- Data loading stays in modules and API clients.
- Access control stays in backend permissions and route-level guards.
- Future v136-v145 screen work should prefer these components before adding one-off UI.
