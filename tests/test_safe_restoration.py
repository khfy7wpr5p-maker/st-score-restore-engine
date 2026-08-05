from __future__ import annotations
import hashlib, tempfile, unittest
from pathlib import Path
import cv2
import numpy as np

from st_score_restore.safe_restoration import RestorationConfig, RestorationError, restore_bytes, restore_path


def encode_png(image: np.ndarray) -> bytes:
    ok, data = cv2.imencode('.png', image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(data)


def synthetic_score(width=1200, height=800, angle=0.0):
    img=np.full((height,width),245,np.uint8)
    for base in (180,420):
        for i in range(5): cv2.line(img,(100,base+i*16),(1100,base+i*16),20,1)
        for x in (250,450,700,900):
            cv2.circle(img,(x,base+32),5,0,-1); cv2.line(img,(x+5,base+32),(x+5,base),0,1)
        cv2.circle(img,(950,base+20),2,0,-1)
    for i in range(6): cv2.line(img,(100,620+i*14),(1100,620+i*14),30,1)
    cv2.putText(img,'3',(300,663),cv2.FONT_HERSHEY_SIMPLEX,0.45,0,1,cv2.LINE_8)
    gradient=np.tile(np.linspace(25,0,width,dtype=np.uint8),(height,1))
    img=np.clip(img.astype(np.int16)-gradient.astype(np.int16),0,255).astype(np.uint8)
    if angle:
        m=cv2.getRotationMatrix2D((width/2,height/2),angle,1.0)
        img=cv2.warpAffine(img,m,(width,height),borderValue=255)
    return img


class SafeRestorationTests(unittest.TestCase):
    def test_deterministic_png_candidate(self):
        src=encode_png(synthetic_score())
        a=restore_bytes(src,source_name='score.png')
        b=restore_bytes(src,source_name='score.png')
        self.assertEqual(a.output_bytes,b.output_bytes)
        self.assertEqual(a.manifest,b.manifest)
        self.assertEqual(hashlib.sha256(src).hexdigest(),a.manifest['sourceDigest']['value'])

    def test_source_is_returned_exactly_after_rejection(self):
        src=encode_png(synthetic_score())
        candidate=restore_bytes(src)
        self.assertIs(candidate.reject(),candidate.source_bytes)
        self.assertEqual(src,candidate.reject())

    def test_staff_tab_and_small_marks_are_not_lightened(self):
        image=synthetic_score()
        src=encode_png(image)
        candidate=restore_bytes(src,config=RestorationConfig(deskew_enabled=False))
        restored=cv2.imdecode(np.frombuffer(candidate.output_bytes,np.uint8),cv2.IMREAD_GRAYSCALE)
        dark=image<80
        self.assertEqual(0,int(np.count_nonzero(restored[dark]>image[dark])))
        self.assertEqual(0,candidate.manifest['safety']['protectedPixelsMadeLighter'])

    def test_operations_can_be_disabled(self):
        image=synthetic_score()
        cfg=RestorationConfig(orientation_enabled=False,deskew_enabled=False,perspective_enabled=False,crop_enabled=False,illumination_enabled=False,denoise_enabled=False,contrast_enabled=False)
        candidate=restore_bytes(encode_png(image),config=cfg)
        restored=cv2.imdecode(np.frombuffer(candidate.output_bytes,np.uint8),cv2.IMREAD_GRAYSCALE)
        self.assertTrue(np.array_equal(image,restored))
        self.assertFalse(any(op['applied'] for op in candidate.manifest['operations']))

    def test_deskew_is_recorded_and_reproducible(self):
        src=encode_png(synthetic_score(angle=2.0))
        candidate=restore_bytes(src,config=RestorationConfig(perspective_enabled=False,crop_enabled=False))
        op=next(x for x in candidate.manifest['operations'] if x['name']=='deskew')
        self.assertTrue(op['enabled'])
        self.assertGreater(op['evidence']['lineCount'],0)
        self.assertLessEqual(abs(op['evidence']['estimatedAngleDegrees']),5.0)

    def test_ambiguous_perspective_requires_review(self):
        src=encode_png(synthetic_score())
        cfg=RestorationConfig(perspective_enabled=True,perspective_min_confidence=1.0)
        candidate=restore_bytes(src,config=cfg)
        self.assertIn(candidate.manifest['status'],{'review_required','candidate_ready'})
        op=next(x for x in candidate.manifest['operations'] if x['name']=='perspective')
        if not op['applied']:
            self.assertIn('ambiguous_perspective',candidate.manifest['safety']['reviewRequiredReasons'])


    def test_high_confidence_perspective_rectification_applies(self):
        page=synthetic_score(900,1200)
        canvas=np.full((1400,1200),40,np.uint8)
        source=np.array([[0,0],[899,0],[899,1199],[0,1199]],np.float32)
        target=np.array([[180,100],[1040,180],[980,1320],[120,1240]],np.float32)
        matrix=cv2.getPerspectiveTransform(source,target)
        warped=cv2.warpPerspective(page,matrix,(1200,1400),borderValue=40)
        mask=cv2.warpPerspective(np.full(page.shape,255,np.uint8),matrix,(1200,1400),borderValue=0)
        canvas[mask>0]=warped[mask>0]
        cfg=RestorationConfig(deskew_enabled=False,perspective_enabled=True,crop_enabled=True)
        candidate=restore_bytes(encode_png(canvas),config=cfg)
        perspective=next(x for x in candidate.manifest['operations'] if x['name']=='perspective')
        crop=next(x for x in candidate.manifest['operations'] if x['name']=='crop')
        self.assertTrue(perspective['applied'])
        self.assertGreaterEqual(perspective['evidence']['confidence'],cfg.perspective_min_confidence)
        self.assertFalse(crop['applied'])
        self.assertIn('crop_satisfied_by_perspective_rectification',crop['warnings'])

    def test_binarization_forces_review(self):
        candidate=restore_bytes(encode_png(synthetic_score()),config=RestorationConfig(binarization_profile='otsu'))
        self.assertEqual('review_required',candidate.manifest['status'])
        self.assertIn('binarized_candidate_requires_review',candidate.manifest['safety']['reviewRequiredReasons'])

    def test_output_formats_have_separate_digests(self):
        src=encode_png(synthetic_score())
        png=restore_bytes(src,output_format='png')
        jpg=restore_bytes(src,output_format='jpeg')
        pdf=restore_bytes(src,output_format='pdf')
        self.assertTrue(pdf.output_bytes.startswith(b'%PDF-1.4'))
        self.assertTrue(jpg.output_bytes.startswith(b'\xff\xd8'))
        self.assertNotEqual(png.manifest['candidate']['digest']['value'],jpg.manifest['candidate']['digest']['value'])
        self.assertNotEqual(hashlib.sha256(src).hexdigest(),pdf.manifest['candidate']['digest']['value'])

    def test_pdf_output_is_deterministic(self):
        src=encode_png(synthetic_score())
        self.assertEqual(restore_bytes(src,output_format='pdf').output_bytes,restore_bytes(src,output_format='pdf').output_bytes)

    def test_digital_pdf_is_not_rasterized(self):
        pdf=b'%PDF-1.4\n1 0 obj << /Type /Page /Font << >> >> endobj\n%%EOF\n'
        with self.assertRaises(RestorationError) as ctx: restore_bytes(pdf,source_name='digital.pdf')
        self.assertEqual('digital_pdf_must_remain_vector',ctx.exception.code)

    def test_scanned_pdf_requires_renderer(self):
        pdf=b'%PDF-1.4\n1 0 obj << /Type /Page /Subtype /Image >> endobj\n%%EOF\n'
        with self.assertRaises(RestorationError) as ctx: restore_bytes(pdf,source_name='scan.pdf')
        self.assertEqual('pdf_renderer_not_available',ctx.exception.code)

    def test_symlink_source_is_rejected(self):
        src=encode_png(synthetic_score(400,300))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'source.png'; link=root/'link.png'
            source.write_bytes(src)
            try: link.symlink_to(source)
            except (OSError,NotImplementedError): self.skipTest('symbolic links unavailable')
            with self.assertRaises(RestorationError) as ctx: restore_path(link,root/'out.png')
            self.assertEqual('symlink_input_not_allowed',ctx.exception.code)

    def test_distinct_output_path_is_required(self):
        src=encode_png(synthetic_score(400,300))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'a.png'; path.write_bytes(src)
            with self.assertRaises(RestorationError) as ctx: restore_path(path,path)
            self.assertEqual('source_overwrite_forbidden',ctx.exception.code)

    def test_restore_path_refuses_existing_output(self):
        src=encode_png(synthetic_score(400,300))
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'a.png'; output=Path(td)/'b.png'
            source.write_bytes(src); output.write_bytes(b'existing')
            with self.assertRaises(RestorationError) as ctx: restore_path(source,output)
            self.assertEqual('derived_output_exists',ctx.exception.code)

    def test_invalid_config_is_rejected(self):
        with self.assertRaises(RestorationError): RestorationConfig(denoise_kernel=7)
        with self.assertRaises(RestorationError): RestorationConfig.from_mapping({'unknown':True})

    def test_candidate_records_all_operations(self):
        candidate=restore_bytes(encode_png(synthetic_score()))
        names=[x['name'] for x in candidate.manifest['operations']]
        self.assertEqual(names,['orientation','deskew','perspective','crop','illumination_normalization','conservative_denoise','clahe_contrast','binarization'])
        self.assertTrue(all(len(x['inputPixelDigest'])==64 and len(x['outputPixelDigest'])==64 for x in candidate.manifest['operations']))


if __name__=='__main__': unittest.main()
