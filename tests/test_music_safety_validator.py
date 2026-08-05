from __future__ import annotations
import unittest
import cv2
import numpy as np

from st_score_restore.music_safety_validator import (
    MusicSafetyValidationError,
    compare_candidate_reports,
    record_teacher_review,
    validate_candidate,
)


def encode_png(image: np.ndarray) -> bytes:
    ok, data = cv2.imencode('.png', image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(data)


def synthetic_score() -> np.ndarray:
    image = np.full((900, 1200), 250, np.uint8)
    for base in (120, 360):
        for i in range(5):
            cv2.line(image, (80, base + i * 16), (1120, base + i * 16), 20, 1)
        for x in (220, 420, 650, 900):
            cv2.circle(image, (x, base + 32), 6, 0, -1)
            cv2.line(image, (x + 6, base + 32), (x + 6, base - 4), 0, 2)
        cv2.circle(image, (1000, base + 24), 2, 0, -1)
        cv2.line(image, (1080, base - 4), (1080, base + 68), 0, 2)
    tab_base = 650
    for i in range(6):
        cv2.line(image, (80, tab_base + i * 18), (1120, tab_base + i * 18), 30, 1)
    cv2.putText(image, '3', (280, tab_base + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    cv2.putText(image, '10', (600, tab_base + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    cv2.line(image, (850, tab_base - 5), (850, tab_base + 95), 0, 2)
    return image


class MusicSafetyValidatorTests(unittest.TestCase):
    def setUp(self):
        self.source_image = synthetic_score()
        self.source = encode_png(self.source_image)

    def test_identical_candidate_passes_and_is_deterministic(self):
        first = validate_candidate(self.source, self.source, source_name='source.png', candidate_name='candidate.png')
        second = validate_candidate(self.source, self.source, source_name='source.png', candidate_name='candidate.png')
        self.assertEqual(first, second)
        self.assertEqual('pass', first['verdict'])
        self.assertFalse(first['automaticApproval'])
        self.assertTrue(first['fallback']['originalAvailable'])

    def test_staff_and_tab_metrics_are_separate(self):
        report = validate_candidate(self.source, self.source)
        self.assertEqual(2, report['geometry']['staff']['sourceSystemCount'])
        self.assertEqual(1, report['geometry']['tab']['sourceSystemCount'])
        self.assertEqual([5, 5], report['geometry']['staff']['sourceLineCounts'])
        self.assertEqual([6], report['geometry']['tab']['sourceLineCounts'])

    def test_symbol_deletion_is_detected(self):
        candidate = self.source_image.copy()
        cv2.rectangle(candidate, (210, 135), (235, 165), 250, -1)
        report = validate_candidate(self.source, encode_png(candidate))
        codes = {item['code'] for item in report['findings']}
        self.assertIn('symbol_dark_pixel_loss', codes)
        self.assertIn(report['verdict'], {'review_required', 'reject'})

    def test_symbol_insertion_is_detected(self):
        candidate = self.source_image.copy()
        cv2.circle(candidate, (520, 285), 7, 0, -1)
        cv2.line(candidate, (527, 285), (527, 250), 0, 2)
        report = validate_candidate(self.source, encode_png(candidate))
        codes = {item['code'] for item in report['findings']}
        self.assertIn('symbol_dark_pixel_invention', codes)
        self.assertIn(report['verdict'], {'review_required', 'reject'})

    def test_symbol_shift_is_detected(self):
        candidate = self.source_image.copy()
        patch = candidate[130:175, 410:445].copy()
        candidate[130:175, 410:445] = 250
        candidate[130:175, 420:455] = np.minimum(candidate[130:175, 420:455], patch)
        report = validate_candidate(self.source, encode_png(candidate))
        codes = {item['code'] for item in report['findings']}
        self.assertTrue({'component_shift', 'thin_component_loss', 'thin_component_invention'} & codes)
        self.assertIn(report['verdict'], {'review_required', 'reject'})

    def test_staff_line_break_is_detected(self):
        candidate = self.source_image.copy()
        cv2.rectangle(candidate, (500, 118), (650, 122), 250, -1)
        report = validate_candidate(self.source, encode_png(candidate))
        codes = {item['code'] for item in report['findings']}
        self.assertIn('staff_line_break', codes)
        self.assertIn(report['verdict'], {'review_required', 'reject'})

    def test_line_count_change_rejects(self):
        candidate = self.source_image.copy()
        cv2.rectangle(candidate, (60, 183), (1140, 190), 250, -1)
        report = validate_candidate(self.source, encode_png(candidate))
        self.assertEqual('reject', report['verdict'])
        self.assertTrue(any('staff_' in reason for reason in report['decision']['rejectReasons']))

    def test_manifest_digest_mismatch_rejects(self):
        manifest = {
            'status': 'candidate_ready',
            'sourceDigest': {'value': '0' * 64},
            'candidate': {'digest': {'value': '1' * 64}, 'teacherApproved': False},
        }
        report = validate_candidate(self.source, self.source, candidate_manifest=manifest)
        self.assertEqual('reject', report['verdict'])
        self.assertIn('candidate_manifest_source_digest_mismatch', report['decision']['rejectReasons'])

    def test_validation_failure_cannot_approve(self):
        with self.assertRaises(MusicSafetyValidationError) as context:
            validate_candidate(self.source, b'not-an-image')
        failure = context.exception.to_dict()
        self.assertEqual('review_required', failure['verdict'])
        self.assertFalse(failure['automaticApproval'])
        self.assertTrue(failure['fallback']['originalAvailable'])

    def test_teacher_review_is_not_training_label(self):
        report = validate_candidate(self.source, self.source)
        reviewed = record_teacher_review(report, 'approved', reviewer_id='teacher-1', notes='Checked visually')
        self.assertEqual('approved', reviewed['teacherReview']['decision'])
        self.assertFalse(reviewed['teacherReview']['trainingLabelCreated'])
        self.assertIsNone(reviewed['teacherReview']['trainingUseConsent'])
        self.assertIsNone(report['teacherReview']['decision'])

    def test_comparator_prefers_pass_and_excludes_reject(self):
        passed = validate_candidate(self.source, self.source)
        damaged = self.source_image.copy()
        cv2.rectangle(damaged, (60, 118), (1140, 126), 250, -1)
        rejected = validate_candidate(self.source, encode_png(damaged))
        comparison = compare_candidate_reports([rejected, passed])
        self.assertEqual('pass_candidate_available', comparison['selectionStatus'])
        self.assertEqual(passed['candidate']['artifactId'], comparison['recommendedCandidateArtifactId'])
        self.assertFalse(comparison['automaticApproval'])

    def test_pdf_candidate_is_decoded(self):
        ok, jpg = cv2.imencode('.jpg', self.source_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        self.assertTrue(ok)
        payload = bytes(jpg)
        pdf = b'%PDF-1.4\n1 0 obj\n<< /Type /XObject /Subtype /Image /Width 1200 /Height 900 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /DCTDecode /Length ' + str(len(payload)).encode() + b' >>\nstream\n' + payload + b'\nendstream\nendobj\n%%EOF\n'
        report = validate_candidate(self.source, pdf)
        self.assertEqual('completed', report['status'])
        self.assertIn(report['verdict'], {'pass', 'review_required'})

    def test_invalid_comparator_input_fails_safe(self):
        with self.assertRaises(MusicSafetyValidationError):
            compare_candidate_reports([{'status': 'failed'}])


if __name__ == '__main__':
    unittest.main()
