#!/usr/bin/env python3
from __future__ import annotations

import json

from st_score_restore.st_restore_image_model import run_synthetic_image_model_drills


def main() -> int:
    result = run_synthetic_image_model_drills()
    assert result["syntheticCandidatePass"] is True
    assert result["trainingRemainsUnauthorized"] is True
    assert result["selectorWillSkipUntrainedModel"] is True
    assert result["productionInferenceAuthorized"] is False
    assert result["stage12EntryAuthorized"] is False
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
