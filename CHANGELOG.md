# Changelog

## Unreleased
- Zip-bomb guard for xlsx/ods and a 60-page cap for PDFs
- Prompt-injection hardening: dataset text declared untrusted, line breaks flattened in cells
- Detection and conversion of text numbers with commas and currency symbols
- Download generated code as a runnable script
- Benchmark runner: `--only` filter, separate partial-results file, no overwrite on API errors
- CI matrix: Python 3.12 and 3.13 on Linux and Windows
- Sheet and table selector for Excel, ODS and SQLite
- Sensitive column masking in prompts
- Data-quality check and one-click text-to-number conversion
- Bring-your-own Groq key and per-session cap for the shared key
- Markdown report download
- Robust CSV/TSV decoding and delimiter detection; defusedxml for XML
- `SANDBOX_MODE=docker` isolation, Dockerfile
- Repair attempt when generated code prints nothing
- Clearer rate-limit and daily-quota messages
- Benchmarks: 30-question basic tier and 21-question hard tier
- CI on Linux and Windows with coverage; scheduled security workflow

## 1.1.0 (sandbox hardening)
- Blocked frame, generator, code and traceback introspection
- Removed `string` from allowed imports
- Blocked additional file-writing helpers; added address-space limit on Linux
