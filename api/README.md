# API boundary

The future versioned HTTP API will expose restoration jobs, candidate results, risk reports, teacher approval, and audit records.

Current transport-neutral boundaries:

- immutable source inspection: `st_score_restore.input_inspection`,
- deterministic candidate engine: `st_score_restore.safe_restoration`,
- source schemas: `schemas/artifact-manifest.schema.json` and `schemas/input-analysis.schema.json`,
- candidate schemas: `schemas/restoration-config.schema.json` and `schemas/restoration-candidate.schema.json`,
- CLIs: `tools/inspect_input.py` and `tools/restore_image.py`.

No HTTP endpoint, upload service, persistence layer, teacher-review endpoint, or derived-output download is implemented yet. Public HTTP contracts still require an ADR and compatibility plan.
