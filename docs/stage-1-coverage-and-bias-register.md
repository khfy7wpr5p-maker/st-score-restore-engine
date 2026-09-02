# Stage 1 Coverage and Bias Register

**Status:** ACCEPTED Stage 1 evidence; historical C16 preserved  
**As of:** 2026-09-02  
**Stage 1 final exit:** PASS / COMPLETE  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY; real-data calibration NOT AUTHORIZED

## Measurement boundary

Coverage and bias findings here are metadata-derived. They do not inspect musical correctness, prove restoration effectiveness or measure OMR accuracy. Later-stage work does not retroactively change these Stage 1 measurements.

Historical C16 remains bound to snapshot `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`, report `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`, result `insufficient`.

Accepted expanded-v2 contains 5 real / 0 synthetic items, 3 development source families and 2 held-out source families. Canonical v2 digests are catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`, snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`, report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Expanded-v2 automatic report deliberately remains `review_required`, `stage1ExitSupported=false`, `stage2EntrySupported=false`. Stage 1 PASS is supplied by separate governance acceptance.

Unsupported claims remain corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission and calibration permission.

## Later-stage boundary

Stage 2 and Stage 3 subsequently completed PASS using their own purpose/custody contracts. Stage 4 framework/governance started through PR #105 at main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`, Run #259. This does not alter this register or `catalog.v2.json`.

The accepted catalog currently has zero granted `safety_calibration` permissions. Held-out data remains evaluation-only and may not tune Stage 4 thresholds or resource limits. Real-data calibration therefore remains fail-closed until separate exact-artifact grants and accepted reference-label provenance exist.