# Infrastructure Directory

`infra/docker`: local compose and container assets.  
`infra/k8s`: team/production manifests and Helm-related files.

Rules:
1. Keep local and production configs separated.
2. Never commit secrets.
3. Every infra change must reference a rollback path in PR description.

