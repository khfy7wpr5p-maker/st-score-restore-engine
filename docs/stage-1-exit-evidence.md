# Stage 1 Exit Evidence

**Status:** PASS / EFFECTIVE / HISTORICAL  
**As of:** 2026-09-02  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Acceptance PR:** #82 — merged  
**Post-merge repository validation:** Run #203 (`33588190548`) — Python 3.11 / 3.12 PASS  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 current state:** COMPLETE / PASS / production-effective  
**Stage 3 current state:** COMPLETE / PASS / production-effective  
**Stage 4 current state:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY; real-data calibration NOT AUTHORIZED

## Decision

Stage 1 final exit is **PASS and effective**. The machine-readable decision remains `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Historical evidence is not rewritten by later stages.

Canonical v2 digests remain catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`, expanded snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`, coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`; C16 remains `insufficient` for its original snapshot.

Accepted aggregate remains 5 real / 0 synthetic items, 3 development families, 2 held-out families, no cross-split source-family leakage, unique exact artifact digests and zero real corpus artifact bytes in ordinary Git.

Stage 1 PASS does not establish representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission or calibration permission.

## Current stage context

Stage 2 and Stage 3 subsequently completed PASS. Stage 4 framework/governance started through PR #105 at main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`, post-merge Run #259 (`33659753403`). This later start does not alter Stage 1 permission metadata. No accepted Stage 1 artifact currently has a granted `safety_calibration` purpose, therefore Stage 4 real-data calibration remains blocked.

The separate sensitive phone-photo path remains blocked pending real `high_assurance_vault` verification.