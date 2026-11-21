# Architecture and threat model

## Flow

```mermaid
flowchart LR
    U[User uploads file] --> R[file_readers.py: parse, clean, quality check]
    R --> M[Mask sensitive columns]
    M --> P[analyst.py: prompt with schema, sample rows, history]
    P --> L[(Groq model)]
    L -->|code or CANNOT_ANSWER| V[sandbox.py: AST validation]
    V --> W[Worker: subprocess or Docker container]
    W -->|printed output and charts| E[analyst.py: explanation from real output]
    E --> UI[streamlit_app.py: answer, charts, report download]
    W -. error or empty output .-> X[one repair attempt] --> V
```

## Threat model

| Threat | Mitigation | Status |
|---|---|---|
| Generated code imports or calls dangerous modules | AST import, name and attribute allow-list; restricted builtins | In place, regression-tested |
| Frame, generator or dunder introspection to reach real builtins | Blocked attribute prefixes and dunder names | In place |
| Code writes files | File-writing helpers blocked; read-only container in Docker mode | Partial in subprocess mode, strong in Docker mode |
| API key theft | Worker environment scrubbed; Docker mode passes no environment | In place, tested |
| Infinite loop or memory bomb | Wall-clock timeout, CPU/file/memory limits (Linux); container limits in Docker mode | Subprocess limits are Linux-only |
| Malicious upload (pickle, XML bombs) | Pickle refused; defusedxml; 25 MB cap | Zip-bomb guard added for xlsx/ods |
| Sensitive values sent to the model | Sensitive-looking columns masked by default; user can choose more | In place; generated code can still use the real values |
| Prompt injection through cell values | Sandbox is the backstop; output explained from real results | Not fully preventable; documented limit |
| Shared API key abuse | Per-session cap; bring-your-own-key | In place; session cap is client-side state only |

## Not covered
Authentication, per-user isolation, persistence, and microVM-level isolation.
