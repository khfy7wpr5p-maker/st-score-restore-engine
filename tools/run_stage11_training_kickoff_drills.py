#!/usr/bin/env python3
from __future__ import annotations

import json

from st_score_restore.stage11_training_dataset import run_training_kickoff_drills


def main() -> int:
    result = run_training_kickoff_drills()
    assert result["admissionPass"] is True
    assert result["heldOutLeakagePrevented"] is True
    assert result["trainingAuthorized"] is True
    assert result["trainingExecutable"] is False
    assert result["weightsEstablished"] is False
    assert result["productionInferenceAuthorized"] is False
    assert result["stage12EntryAuthorized"] is False
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
