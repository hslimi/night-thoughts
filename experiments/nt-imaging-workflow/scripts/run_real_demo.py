from __future__ import annotations

import os

from nt_imaging.cli import run_local

if os.getenv("INFERENCE_MODE") != "REAL":
    raise SystemExit("Real demonstration requires explicit INFERENCE_MODE=REAL")
raise SystemExit(
    run_local(
        type(
            "Args",
            (),
            {
                "source": "fixtures/synthetic/chest_clean.png",
                "modality": "XR",
                "decision": "APPROVE",
                "reviewer": "Demo Reviewer",
                "note": "Synthetic real-provider demonstration",
                "fault_profile": None,
            },
        )()
    )
)
