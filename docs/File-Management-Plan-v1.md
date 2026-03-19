# File Management Plan v1

## 1. Objective
Keep repository structure predictable, transferable, and release-safe from day 1.

## 2. Directory Layout
```text
.
├─ app/
│  ├─ api/
│  ├─ compatibility/
│  ├─ core/
│  ├─ memory/
│  ├─ orchestration/
│  ├─ providers/
│  └─ retrieval/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ compatibility/
│  ├─ e2e/
│  └─ fixtures/
├─ configs/
│  ├─ profiles/
│  └─ policies/
├─ infra/
│  ├─ docker/
│  └─ k8s/
├─ scripts/
├─ examples/
│  ├─ cli/
│  ├─ sdk-python/
│  └─ sdk-js/
├─ data/
├─ logs/
└─ docs/
```

## 3. Ownership and Boundaries
1. `app/*`: production code only.
2. `tests/*`: test code and fixtures only.
3. `configs/*`: non-secret config templates and policy definitions.
4. `infra/*`: deployment/runtime infrastructure assets.
5. `scripts/*`: repeatable operational scripts.
6. `examples/*`: integration examples and client samples.
7. `data/*`, `logs/*`: runtime artifacts, excluded from version control.

## 4. Naming Rules
1. Use lowercase kebab-case for docs and config files.
2. Use snake_case for Python modules/files.
3. Prefix major docs with stable suffix (`-v1`, `-v2`) when versioned.
4. Use explicit scope in filenames (for example `compatibility-*.md`, `api-*.md`).

## 5. File Lifecycle Rules
1. New feature requires:
   - code under `app/*`
   - tests under `tests/*`
   - docs update under `docs/*`
2. Schema/config change requires:
   - doc update
   - migration note
   - rollback note
3. Deleting files requires:
   - reason in PR
   - impact note in `MESSAGES.md`

## 6. Change Tracking Rules
1. Every meaningful operation batch updates `MESSAGES.md`.
2. Every milestone-level change updates `docs/Progress-Tracker.md`.
3. Root `README.md` remains source of truth for current execution entry points.

## 7. Compatibility-First File Rules
1. Compatibility adapters live in `app/compatibility/`.
2. Protocol conformance tests live in `tests/compatibility/`.
3. Example client usage must be mirrored in `examples/`.

## 8. Pre-Release File Checklist
1. No secrets committed.
2. No runtime db/index/log artifacts committed.
3. All new top-level files linked from `README.md` or `docs/README.md`.
4. Added/changed modules have corresponding tests.
5. Documentation references remain valid.

## 9. Initial Implementation Status
This structure is created and reserved as project baseline.  
Code implementation has not started yet.

