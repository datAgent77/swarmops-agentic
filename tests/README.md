# tests/

Cross-cutting / end-to-end tests that span apps. The full demo-flow E2E test is
added in **P14**. Per-app unit tests live next to their code:

- Backend: `apps/api/tests/` (run with `make test`).
- Frontend: colocated under `apps/web` (added in later phases).
