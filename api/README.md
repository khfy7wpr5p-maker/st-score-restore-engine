# API boundary

The future versioned HTTP API will expose restoration jobs, candidate results, risk reports, teacher approval, and audit records.

Milestone M1 now defines a transport-neutral, read-only input-inspection contract:

- immutable source artifacts: `schemas/artifact-manifest.schema.json`
- structural analysis: `schemas/input-analysis.schema.json`
- Python boundary: `st_score_restore.inspect_path` and `inspect_bytes`
- CLI boundary: `python tools/inspect_input.py <path>`

No HTTP endpoint, upload service, persistence layer, restoration operation, or derived-output download is implemented yet. Public HTTP contracts still require an ADR and compatibility plan.
