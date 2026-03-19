# Deployment Guide v1

## 1. Local Single-Node Deployment (Primary)

## 1.1 Components
1. LM Studio runtime with local model.
2. ContextLedger API service.
3. SQLite DB.
4. Local vector index.
5. Optional async worker for indexing/summarization.

## 1.2 Startup Sequence
1. Start LM Studio and load model.
2. Confirm model endpoint is reachable.
3. Start ContextLedger service.
4. Start async worker (recommended).
5. Run health check.

## 1.3 Health Verification
1. `GET /v1/health` returns `status=ok`.
2. Send one `/v1/chat` request and verify answer and audit log.
3. Call `/v1/resume` to verify snapshot generation.
4. Verify worker heartbeat and queue lag metrics.

## 2. Docker Compose Layout (v1)
```text
docker-compose.yml
services:
  app:
    memory-proxy-api
  redis:
    optional for queue/cache
volumes:
  ./data
```

Note: LM Studio process can run outside Docker on host.

## 3. Team Deployment (Phase C)
1. API replicas behind reverse proxy.
2. Worker service for memory extraction and indexing.
3. Postgres as primary DB.
4. Qdrant as vector DB.
5. Redis for cache and broker.

## 4. Security Baseline
1. Bind service to private network by default.
2. Protect API with token in non-local mode.
3. Store secrets in environment or secret manager.
4. Disable debug endpoints in production.
5. Enforce project-root path allowlist for file operations.

## 5. Backup and Recovery
1. SQLite mode: file backup per day.
2. Postgres mode: logical dump + WAL strategy.
3. Vector store snapshot aligned with SQL backup timestamp.
4. Recovery drill every release cycle.
