import copy
import hashlib
import json
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore.stage11_v2a_shadow_corpus import (
    FIRST_REAL_DATASET_ITEM_ID,
    Stage11V2aShadowCorpusError,
    build_shadow_corpus_plan,
    eligible_shadow_corpus_items,
    run_nonheldout_shadow_corpus,
    validate_shadow_corpus_execution_evidence,
)
from st_score_restore.stage11_v2a_shadow_corpus_current_truth import (
    Stage11V2aShadowCorpusCurrentTruthError,
    validate_stage11_v2a_shadow_corpus_current_truth,
)
from st_score_restore.stage11_v2a_shadow_handoff import Stage11V2aShadowObserver
from st_score_restore.stage11_v2a_staging_api import EXPECTED_PACKAGE_SHA256, encode_grayscale_png

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-corpus-evidence.v1.json"
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CORPUS_CURRENT_TRUTH.json"


def _png() -> bytes:
    image = np.full((96, 144), 240, dtype=np.uint8)
    for y in (20, 26, 32, 38, 44):
        image[y:y + 1, 8:136] = 20
    cv2.circle(image, (52, 32), 4, 15, -1)
    cv2.line(image, (56, 32), (56, 15), 15, 1)
    return encode_grayscale_png(image)


def _item(raw: bytes, *, item_id: str = "dataset.item.synthetic-shadow.v1", split: str = "development", kind: str = "png", media_type: str = "image/png", quality: str = "granted", source_kind: str = "public_domain"):
    return {
        "datasetItemId": item_id,
        "sourceFamilyId": f"source.family.{item_id}.v1",
        "eligibilityClass": "open_corpus",
        "artifact": {"state": "external_available", "sha256": hashlib.sha256(raw).hexdigest(), "byteSize": len(raw)},
        "provenance": {"sourceKind": source_kind, "rightsReview": {"status": "approved"}},
        "privacy": {"classification": "none"},
        "input": {"kind": kind, "mediaType": media_type, "notationKinds": ["staff"], "pageCount": 1, "degradations": ["none"]},
        "permissions": {"quality_evaluation": {"status": quality}},
        "split": split,
        "review": {"status": "approved"},
        "revocation": {"status": "not_revoked"},
    }


def _identity_handle(body, metadata):
    return body, {
        "requestId": metadata["requestId"],
        "sourceDataKind": metadata["sourceDataKind"],
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "tileCount": 1,
        "requestSha256": hashlib.sha256(body).hexdigest(),
        "responseSha256": hashlib.sha256(body).hexdigest(),
        "networkRouteRegistered": False,
        "existingHttpApiModified": False,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }


class Stage11V2aShadowCorpusTests(unittest.TestCase):
    def test_repository_catalog_selects_only_approved_nonheldout_supported_items(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        selected = {item["datasetItemId"] for item in eligible_shadow_corpus_items(catalog)}
        self.assertIn(FIRST_REAL_DATASET_ITEM_ID, selected)
        self.assertIn("dataset.item.wikimedia-guitar-technical-exercise-no1.v1", selected)
        self.assertNotIn("dataset.item.imslp82860-chopin-op69.v2", selected)
        self.assertNotIn("dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1", selected)

    def test_plan_fails_closed_for_heldout_or_ungranted_items(self):
        raw = _png()
        heldout = _item(raw, item_id="dataset.item.heldout.v1", split="held_out")
        ungranted = _item(raw, item_id="dataset.item.ungranted.v1", quality="not_requested")
        catalog = {"items": [heldout, ungranted]}
        with self.assertRaises(Stage11V2aShadowCorpusError):
            build_shadow_corpus_plan(catalog, ["dataset.item.heldout.v1"])
        with self.assertRaises(Stage11V2aShadowCorpusError):
            build_shadow_corpus_plan(catalog, ["dataset.item.ungranted.v1"])

    def test_runner_executes_observational_png_lane_without_selection_or_training(self):
        raw = _png()
        item = _item(raw)
        plan = build_shadow_corpus_plan({"items": [item]}, [item["datasetItemId"]])
        result = run_nonheldout_shadow_corpus(
            plan,
            {item["datasetItemId"]: raw},
            Stage11V2aShadowObserver(_identity_handle),
        )
        self.assertEqual(1, result["pageObservationCount"])
        self.assertEqual("development", result["corpus"][0]["split"])
        self.assertFalse(result["aggregate"]["qualityDecisionMade"])
        self.assertFalse(result["aggregate"]["automaticPromotionPerformed"])
        self.assertFalse(result["safety"]["heldOutAccessed"])
        self.assertFalse(result["safety"]["trainingPerformed"])
        self.assertFalse(result["authorization"]["productionInferenceAuthorized"])
        self.assertFalse(result["authorization"]["stage12EntryAuthorized"])

    def test_runner_rejects_wrong_exact_source_bytes(self):
        raw = _png()
        item = _item(raw)
        plan = build_shadow_corpus_plan({"items": [item]}, [item["datasetItemId"]])
        corrupted = bytearray(raw)
        corrupted[-1] ^= 1
        with self.assertRaises(Stage11V2aShadowCorpusError):
            run_nonheldout_shadow_corpus(
                plan,
                {item["datasetItemId"]: bytes(corrupted)},
                Stage11V2aShadowObserver(_identity_handle),
            )

    def test_committed_real_nonheldout_execution_evidence_passes(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        result = validate_shadow_corpus_execution_evidence(payload)
        self.assertTrue(result["realNonheldoutCorpusObserved"])
        self.assertEqual(4, result["pageObservationCount"])
        self.assertEqual(1, result["sourceFamilyCount"])
        self.assertFalse(result["productionInferenceAuthorized"])

    def test_evidence_cannot_be_relabeled_heldout_or_promoted(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        heldout = copy.deepcopy(payload)
        heldout["corpus"][0]["split"] = "held_out"
        with self.assertRaises(Stage11V2aShadowCorpusError):
            validate_shadow_corpus_execution_evidence(heldout)
        promoted = copy.deepcopy(payload)
        promoted["authorization"]["productionInferenceAuthorized"] = True
        with self.assertRaises(Stage11V2aShadowCorpusError):
            validate_shadow_corpus_execution_evidence(promoted)

    def test_current_truth_passes_and_stage12_remains_closed(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        result = validate_stage11_v2a_shadow_corpus_current_truth(payload)
        self.assertTrue(result["realNonheldoutCorpusObserved"])
        self.assertEqual("broaden-nonheldout-shadow-corpus-source-family-coverage", result["nextSafeBoundary"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_current_truth_cannot_authorize_stage12(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        payload["authorization"]["stage12EntryAuthorized"] = True
        with self.assertRaises(Stage11V2aShadowCorpusCurrentTruthError):
            validate_stage11_v2a_shadow_corpus_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
