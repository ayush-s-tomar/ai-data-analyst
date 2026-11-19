# Security policy

## Scope
AI Data Analyst runs model-generated Python on uploaded data. The main risks are code escaping the sandbox,
leaking the API key, and resource exhaustion.

## What is in place
- AST allow-list for imports, attributes and builtins, with dunder and frame-introspection access blocked
- Separate worker process with a scrubbed environment, wall-clock timeout, CPU, file-size and memory limits (Linux)
- Pickle uploads are refused, and XML is parsed with defusedxml
- Regression tests for each known escape route (`tests/test_sandbox*.py`)

## Known limits
This is defence in depth, not a hardened container sandbox. The worker shares the host with the app, so do not
upload sensitive data to the public demo. Container or microVM isolation is on the roadmap.

## Reporting a vulnerability
Please open a private security advisory on GitHub (Security tab, "Report a vulnerability") rather than a public issue.
Include steps to reproduce. Expect a first response within a week.
