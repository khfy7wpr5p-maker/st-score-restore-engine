# Branch and Change Policy

**Status:** Approved governance baseline  
**Applies to:** `st-score-restore-engine`

## 1. Protected direction

`main` represents the latest reviewed baseline. Implementation work should arrive through focused pull requests.

Direct commits to `main` are reserved for exceptional repository administration or explicitly approved emergency corrections. Routine code, model, API, test, and architecture changes use branches.

## 2. Branch naming

Use short, purpose-specific names:

- `docs/<topic>`
- `feature/<capability>`
- `fix/<defect>`
- `test/<scope>`
- `experiment/<research-question>`
- `release/<version>`

Automated assistant branches may use `agent/<description>`.

## 3. Pull-request size

Each pull request should implement or document one coherent outcome. Separate unrelated cleanup, dependency upgrades, model experiments, and public-contract changes.

A pull request that changes the restoration pipeline must identify:

- accepted input types,
- output and audit effects,
- musical-preservation risks,
- fallback and rollback behavior,
- teacher-approval impact,
- training-data impact.

## 4. Review gates

Before merge, verify the gates relevant to the change:

1. **Repository boundary:** no unrelated application logic is introduced.
2. **Original preservation:** the original input remains immutable.
3. **Deterministic baseline:** classical processing remains available as a fallback.
4. **Music safety:** no notation or TAB mutation is accepted solely for visual quality.
5. **Auditability:** engine, parameters, model version, risks and approval state are recorded.
6. **Privacy and consent:** user documents are not silently retained or used for training.
7. **License review:** new libraries, models and weights have compatible terms.
8. **Verification:** tests and checks provide fresh evidence.

## 5. Experimental work

Experimental algorithms and AI models must be disabled by default and clearly separated from trusted production paths. Their outputs must not flow automatically to OMR, MusicXML, SesliTab or other consumers until validation criteria are met.

## 6. API compatibility

Public contracts are versioned. Breaking changes require:

- a written architecture decision,
- migration notes,
- consumer impact analysis,
- a compatibility or transition plan.

## 7. Merge policy

Prefer squash merge for focused feature and documentation pull requests. The final commit message should describe the outcome rather than individual editing steps.

Do not merge a draft pull request. Do not merge when required safety evidence is missing, even when the visual result appears improved.

## 8. Rollback

Every release that changes restoration selection, validation thresholds or model behavior must retain a documented route to the previous trusted version.
