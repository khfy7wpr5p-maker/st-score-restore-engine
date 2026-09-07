# ADR 0026 — Stage 11 DeepScoresV2 Dense rights-cleared training source

Date: 2026-09-07
Status: Accepted for non-production Stage 11 model training

## Context

Camera-PrIMuS remains excluded from commercial model training because its image-package commercial-training rights were not established. The project owner uploaded the official `ds2_dense.tar.gz` DeepScoresV2 Dense archive to the approved Google Drive training-data folder and authorized continuation of Stage 11 training.

The connected Drive source was observed as file id `1QjvmZSpWgnc8wdfcwfmcXTdibXQnriJS`, name `ds2_dense.tar.gz`, size `741814529` bytes, in folder `ST_SCORE_RESTORE_STAGE11_TRAINING_DATA` (`1Ov_cUo6O1guuegX1GiqrRlHvTtCjHpvy`). The connector cannot materialize this 741 MB file because its raw-download limit is 256 MB; therefore exact-byte checksum verification must occur inside Colab after Drive mount.

DeepScoresV2's Zenodo record identifies the dense archive, DOI `10.5281/zenodo.4012193`, 1,714 dense images and MD5 `7237318e381e6e0848ec30eb82decb83`. The ZHAW research-data record for the same dataset/DOI records the rights as CC BY 4.0. CC BY 4.0 permits commercial reuse/adaptation subject to attribution, so this source is admitted for the authorized Stage 11 training purpose with attribution preserved.

## Decision

1. DeepScoresV2 Dense becomes the active rights-cleared Stage 11 baseline source; Camera-PrIMuS remains commercially excluded.
2. The official 352-image DeepScores test split remains held-out. It is never used for training, development tuning, architecture choice or threshold calibration.
3. The official 1,362-image train split is further divided into train/development by stable source family. The filename prefix before `-aug-` is treated as the source-family identity. Any family present in the official test split is excluded from train/development entirely.
4. Clean DeepScores images are restoration targets. Degraded sources are generated deterministically on the fly using bounded rotation, perspective, blur, illumination, brightness/contrast, Gaussian noise and JPEG compression.
5. Training uses 512×512 ink-aware crops rather than shrinking full high-resolution pages to a small raster, reducing risk to stems, beams, dots, accidentals, ledger lines and other thin symbols.
6. The first baseline remains a Residual U-Net trained with pixel L1 plus Sobel edge-preservation loss. It uses no downloaded or external pretrained weights.
7. The Colab notebook must verify archive size and official MD5 before extraction. Tar members are checked against path traversal, links and device entries before extraction.
8. Checkpoints (`last.pt`, `best.pt`) and run evidence are written to Google Drive. A matching archive MD5 and training-config digest are required before checkpoint resume.
9. Held-out final evaluation defaults to off and requires a separately frozen configuration record before it can be enabled.
10. Stage 9A preservation evidence, Stage 9 comparison and Stage 10 selection remain mandatory before any release decision. Production inference, automatic final selection, model publication and Stage 12 remain unauthorized.

## Attribution obligation

Any model/release documentation that relies on this source must preserve attribution to DeepScoresV2 authors Lukas Tuggener, Yvan Putra Satyawan, Alexander Pacha, Jürgen Schmidhuber and Thilo Stadelmann, DOI `10.5281/zenodo.4012193`, and the CC BY 4.0 notice.

## Current execution boundary

The Drive archive is present and the training pipeline is ready. Training is **not** yet claimed as started because the exact archive MD5 has not yet been verified inside a real Colab GPU session and no checkpoint/run evidence exists. The next valid transition occurs only after Colab writes verified `archive_identity.json` and actual GPU training evidence/checkpoints to Drive.
