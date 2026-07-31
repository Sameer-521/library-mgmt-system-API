# TODOS

## Endpoints

- [ ] **GET /books** — currently returns empty list `{"books": []}`. Implement listing with pagination (limit/offset) and optional search/filter by title, author, isbn.
- [ ] **DELETE /books** — bare stub. Implement soft delete (mark books as inactive rather than removing from DB).
- [ ] **View user schedules** — users can schedule books but there's no endpoint to view their active/completed schedules.
- [ ] **View active loans** — staff endpoint to list all active loans across users.

## Features / Improvements

- [ ] **Book copy status lifecycle** — after `return_book`, the copy goes to `IN_CHECK`. Need staff endpoint to move it from `IN_CHECK` → `AVAILABLE` (inspection flow).
- [ ] **Pagination on all list endpoints** — currently every list endpoint returns raw scalars with no limit/offset.
- [ ] **Maintenance utilities** — auto-expire stale schedules (e.g., daily cleanup of unconsumed schedules past expiry), clear old audit logs.
- [ ] **Configurable late fee** — currently hardcoded at 100/day (`services.py:237`). Move to settings/DB.

## Tests

- [ ] `test_books_router.py` — expand coverage (soft delete, pagination, return-book flow edge cases).
- [ ] `test_users_router.py` — expand coverage (staff creation, non-staff listing with pagination).
- [ ] Add `test_services.py` — unit test service layer in isolation.
- [ ] Add integration tests for the full loan → return → inspection workflow.

## Docs / Housekeeping

- [ ] Expand `README.md` — currently just says `# library-api`. Document endpoints, auth flow, setup instructions.
