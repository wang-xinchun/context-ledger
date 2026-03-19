# Data Model v1

## 1. Tables

## 1.1 `projects`
- `id` (pk)
- `name`
- `description`
- `created_at`
- `updated_at`

## 1.2 `sessions`
- `id` (pk)
- `project_id` (fk -> projects.id)
- `title`
- `started_at`
- `ended_at` (nullable)
- `schema_version`

## 1.3 `turns`
- `id` (pk)
- `project_id` (fk)
- `session_id` (fk)
- `role` (`user` | `assistant` | `system`)
- `content`
- `token_count`
- `request_id` (unique)
- `created_at`

## 1.4 `memories`
- `id` (pk)
- `project_id` (fk)
- `session_id` (fk)
- `turn_id` (fk)
- `type` (`fact` | `decision` | `constraint` | `todo` | `risk`)
- `content`
- `importance` (1..5)
- `source_ref`
- `schema_version`
- `created_at`

## 1.5 `memory_vectors`
- `id` (pk)
- `memory_id` (fk -> memories.id)
- `vector_ref` (faiss/qdrant index reference)
- `dim`
- `created_at`

## 1.6 `timeline_events`
- `id` (pk)
- `project_id` (fk)
- `memory_id` (nullable fk)
- `event_type`
- `content`
- `created_at`

## 1.7 `audit_logs`
- `id` (pk)
- `project_id` (fk)
- `session_id` (fk)
- `request_id`
- `provider_name`
- `latency_ms`
- `continuations`
- `quality_score`
- `input_tokens`
- `output_tokens`
- `status`
- `created_at`

## 2. Indexes
1. `idx_turns_project_session_created_at`
2. `idx_memories_project_type_created_at`
3. `idx_timeline_project_created_at`
4. `idx_audit_project_created_at`

## 3. Migration Rules
1. All schema changes go through Alembic migration.
2. Every migration includes backward compatibility note.
3. Breaking changes require API version bump plan.

