# Development Guide v1

## 1. Repository Structure (planned)
```text
.
├─ app/
│  ├─ api/
│  ├─ core/
│  ├─ providers/
│  ├─ memory/
│  ├─ retrieval/
│  └─ orchestration/
├─ tests/
├─ docs/
└─ scripts/
```

Reference: see [File Management Plan v1](./File-Management-Plan-v1.md) for ownership and lifecycle rules.

## 2. Coding Rules
1. Keep provider interface stable; add adapters instead of branching core logic.
2. Every module should emit structured logs with request id.
3. No direct SQL in business handlers; use repository layer.
4. Add unit tests for any budget or continuation logic changes.
5. New files must be created under the designated module directory, not in root.

## 3. Branch and Commit Strategy
1. Branch naming: `feat/*`, `fix/*`, `docs/*`, `chore/*`.
2. Conventional commit style recommended.
3. Do not merge without passing lint and tests.

## 4. Pull Request Checklist
1. API contract updated if endpoint behavior changes.
2. Migration added for schema changes.
3. Test coverage updated.
4. Docs updated in `docs/`.

## 5. Definition of Done
1. Feature works end-to-end.
2. Tests pass locally.
3. Observability fields complete.
4. Release notes drafted.
