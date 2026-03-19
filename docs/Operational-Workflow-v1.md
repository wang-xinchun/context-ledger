# Operational Workflow v1

## 1. Purpose
Define a single operational workflow for daily collaboration so structure, progress tracking, and handover stay consistent.

## 2. Repository Structure (Execution View)
```text
.
|-- app/          # production code
|-- tests/        # test code and fixtures
|-- configs/      # non-secret config templates and policies
|-- infra/        # docker/k8s and deployment assets
|-- scripts/      # repeatable automation scripts
|-- examples/     # integration and SDK examples
|-- data/         # runtime artifacts (gitignored)
|-- logs/         # runtime artifacts (gitignored)
`-- docs/         # product/design/engineering governance docs
```

Reference baseline: `docs/File-Management-Plan-v1.md`

## 3. Source-of-Truth Files
1. `README.md`
   - Project control panel and immediate next actions.
   - Should always reflect current phase and execution priorities.
2. `docs/Progress-Tracker.md`
   - Milestone board, risks, decisions, and session-level progress.
   - Primary place for phase-level status updates.
3. `MESSAGES.md`
   - Append-only cross-session operation log.
   - Record concrete changes, files touched, decisions, next actions, blockers.
4. `docs/File-Management-Plan-v1.md`
   - Directory ownership, naming, and file lifecycle rules.
5. `docs/Handover-Guide-v1.md`
   - Transfer checklist and coding-start prerequisites.

## 4. Update Triggers and Rules
1. For each meaningful operation batch:
   - Append one entry to `MESSAGES.md`.
2. For milestone-level changes (status, risk, decision, or major scope shift):
   - Update `docs/Progress-Tracker.md`.
3. For architecture/API/config/schema behavior changes:
   - Update corresponding docs under `docs/` in the same batch.
4. For new top-level files or major docs:
   - Add links in `README.md` or `docs/README.md`.
5. For schema/config changes:
   - Include migration impact and rollback notes.

## 5. Session Cadence (Do This Every Session)
1. Session start:
   - Read `README.md`, `docs/Progress-Tracker.md`, `MESSAGES.md`.
   - Confirm current milestone and immediate next action.
2. During execution:
   - Keep code in `app/*`, tests in `tests/*`, docs in `docs/*`.
   - Maintain provider-agnostic core boundaries.
3. Session end:
   - Sync `README.md` control panel with `docs/Progress-Tracker.md`.
   - Append `MESSAGES.md` entry with next action and blockers.
   - If handover is expected, validate `docs/Handover-Guide-v1.md` checklist.

## 6. Current Implementation Priority Order
1. M1 scaffold and runnable backend entrypoint.
2. `/v1/health`.
3. Minimal `/v1/chat`.
4. Compatibility gateway skeleton and conformance tests.
5. Context budget and continuation pipeline.
