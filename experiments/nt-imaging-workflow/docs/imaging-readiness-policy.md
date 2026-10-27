# Imaging Readiness Agent policy

The machine-readable default is [`policies/cxr_preparation_v2.json`](../policies/cxr_preparation_v2.json). The implementation is `src/nt_imaging/imaging/readiness.py`; preparation code version is `imaging-readiness-v2`. The agent is deterministic and makes no diagnostic finding.

## Input contract

Readiness receives only a PHI-cleared opaque artifact ID, a supported CR/DX/XR profile, the versioned policy, and run/thread identifiers. A non-clear PHI result, unsupported modality, or caller-supplied path cannot reach it. The source and PHI-cleared objects are never overwritten.

Supported scope is one frame of a CR/DX chest radiograph or a PNG/JPEG declared `XR`. DICOM is limited to uncompressed little-endian transfer syntax, supported CR/DX SOP classes, one grayscale frame, and 8/10/12/16 stored bits. Other modalities, frames, compression, sequences (apart from one VOI LUT sequence), and undecodable content fail closed.

## Ordered operations

1. Verify decoded dimensions, channels, bit depth, signedness, transfer syntax, finite values, and resource limits.
2. Apply DICOM Modality LUT/rescale slope/intercept before display mapping.
3. Apply the first documented VOI LUT or first calibrated window. VOI LUT inputs must be integral. Without VOI, map the theoretical signed/unsigned range after rescale; do not use generic per-image min-max normalization.
4. Invert MONOCHROME1 after display mapping; leave MONOCHROME2 unchanged.
5. Preserve decoded orientation without arbitrary flips or laterality changes.
6. Preserve aspect ratio. If the largest dimension exceeds 1024 pixels, use bounded SimpleITK BSpline resampling. No stretching or routine crop occurs.
7. Create a lossless PNG model input and a separate, at-most-512-pixel display thumbnail. The thumbnail is never the model input.
8. Write source/derivative/thumbnail lineage and the preparation receipt with atomic replacement.
9. Decode and verify the derivative, dimensions, nonuniform intensity, saturation, and recorded hash. Re-run burned-in text screening on derived pixels before drafting.

Raster input uses the PHI-screened, orientation-normalized 8-bit grayscale derivative. No universal contrast enhancement occurs.

## Prohibited default transforms

- CLAHE or histogram equalization.
- Sharpening or denoising.
- Elastic transforms or random augmentation.
- Automatic lesion-region or destructive cropping.
- Lossy recompression.
- Arbitrary orientation/laterality flips.
- Generic per-image min-max normalization.
- Treating visual improvement as evidence of diagnostic preservation.

Any future experiment profile needs a new policy version, explicit provenance, and separate evidence. MONAI is a possible future study-level 2D/3D transform framework, not a current dependency. PyTorch is not installed.

## Receipt and idempotency

The readiness key binds source SHA-256, policy version, and preparation code version. The prepared ID and receipt ID derive from that key; the thumbnail ID is deterministic too. A replay reuses the derivative only when source, policy, code, actual file hash, and decoded dimensions all match. A mismatch blocks reuse rather than silently accepting an incompatible artifact.

Receipts include:

- run/thread, source/prepared/thumbnail IDs and SHA-256 hashes;
- policy and preparation-code versions;
- source dtype, stored bits, signedness, transfer syntax;
- source and prepared dimensions, intensity min/max/p01/p99, black/white fractions;
- ordered operations, warnings, library versions, timing, and immutable lineage.

`IMAGE_PREPARATION_FAILED` means no model call and no export. `READY` plus derived PHI `CLEAR` is required before drafting and is independently rechecked by export. Readiness does not prove diagnostic preservation, clinical suitability, anonymization, or model accuracy.
