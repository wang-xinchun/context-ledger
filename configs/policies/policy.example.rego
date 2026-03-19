package memoryproxy.policy

default allow = false

# Example rule: block delete outside project root
allow {
  input.action == "delete"
  startswith(input.path, input.project_root)
}

# Example rule: allow read in project root
allow {
  input.action == "read"
  startswith(input.path, input.project_root)
}

