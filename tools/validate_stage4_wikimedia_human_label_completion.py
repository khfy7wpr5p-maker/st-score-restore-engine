from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_wikimedia_reference_gate import (
    build_wikimedia_reference_completion_candidate,
    validate_wikimedia_review_work_package,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
EXPECTED_FINDINGS = {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise", "compression"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(WORK_PACKAGE.exists(), "Wikimedia work package missing")
    require(COMPLETION.exists(), "Wikimedia human-label completion evidence missing")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    package = load(WORK_PACKAGE)
    completion = load(COMPLETION)

    try:
        validate_wikimedia_review_work_package(package)
    except Exception as exc:  # validation failure must fail closed
        failures.append(f"committed Wikimedia work package is not pristine: {exc}")

    bundle = completion.get("bundle", {})
    records = bundle.get("records", [])
    require(len(records) == 7, "completion evidence must contain exactly seven human labels")
    require({row.get("findingType") for row in records} == EXPECTED_FINDINGS, "completion finding taxonomy drifted")
    require({row.get("referenceLabel") for row in records} == {"clear"}, "recorded human labels drifted from the supplied all-clear review")
    require(completion.get("labelCounts") == {"clear": 7, "not_assessed": 0, "possible": 0, "probable": 0}, "completion label counts drifted")

    completed_reviews = [
        {
            "labelId": row.get("labelId"),
            "observationId": row.get("observationId"),
            "findingType": row.get("findingType"),
            "referenceLabel": row.get("referenceLabel"),
            "reviewerReference": row.get("reviewerReference"),
            "provenanceReference": row.get("provenanceReference"),
            "reviewedOn": row.get("reviewedOn"),
        }
        for row in records
    ]

    try:
        rebuilt = build_wikimedia_reference_completion_candidate(package, completed_reviews)
    except Exception as exc:
        failures.append(f"completion evidence cannot be rebuilt by the fail-closed ingestion gate: {exc}")
    else:
        require(rebuilt == completion, "committed completion evidence does not exactly match deterministic ingestion output")

    assertions = completion.get("assertions", {})
    require(assertions.get("humanLabelsPresent") is True, "completion evidence lost humanLabelsPresent=true")
    for key in (
        "labelsAutomaticallyGenerated",
        "modelPredictionsUsedAsReferenceLabels",
        "referenceBundleAccepted",
        "candidateDerivationEligible",
        "expansionCalibrationExecutionAuthorized",
        "expansionCalibrationExecuted",
        "heldOutIncludedInDevelopmentReview",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe completion assertion became true: {key}")

    package_reviews = package.get("item", {}).get("pages", [{}])[0].get("reviews", [])
    for row in package_reviews:
        require(
            all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")),
            f"immutable work-package slot was populated: {row.get('findingType')}",
        )

    if failures:
        print("Stage 4 Wikimedia human-label completion validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 Wikimedia human-label completion validation: PASS")
    print("- seven user-supplied human_expert_review labels are frozen as clear")
    print("- work package remains pristine and separate")
    print("- reference acceptance, derivation, calibration execution, Stage 4 PASS and Stage 5 entry remain false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
