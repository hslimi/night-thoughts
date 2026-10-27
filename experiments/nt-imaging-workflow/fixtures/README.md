# Synthetic fixtures

All generated images are artificial pixel patterns, not patient data and not clinically meaningful radiographs. The `R` marker is an allowed acquisition marker. Files with names containing `phi`, `private`, or `unexpected_text` contain invented test values only. Run `make fixtures` to regenerate deterministic fixtures and their hashes. The oversized fixture is a safe parser-limit test and must not be sent to inference.

The fixture generator and generated artificial fixtures are original project work released under CC0-1.0. No external dataset, patient image, or third-party medical-image fixture is included. `chest_mono1.dcm` and `chest_signed_voi.dcm` exercise photometric, signed-pixel, rescale, and windowing behavior with the same synthetic chest-like pattern.
