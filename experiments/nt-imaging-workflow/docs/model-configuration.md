# Model configuration

Tested on macOS 27.0.1, Python 3.11.17, oMLX 0.7.0, LangGraph 1.2.17, and the exact versions in `uv.lock`. No Agent Server or hosted Studio CLI is required. The discovered local IDs were `MedMO-8B-Next` for vision and `Qwen3.5-9B-MLX-4bit` for text. These are local configuration, not universal defaults.

Run `./scripts/configure_models.sh`. It securely reads only the existing inference key in memory, lists authenticated `/v1/models` results, and writes only endpoint/model IDs to ignored `.env`. `CONFIGURE_NONINTERACTIVE=1 OMLX_VISION_MODEL=<exact-id> OMLX_TEXT_MODEL=<exact-id>` supports automation. Never put a key in screenshots or evidence.

`make doctor` checks platform, environment isolation, existing daemon/listener status, memory information, OCR, model inventory, and minimal real text/image calls. A real failure exits non-zero. Model availability and free memory are not performance guarantees. Do not unload other applications' models or restart oMLX for this project.

Real provider calls use oMLX's tested native `json_schema` response format for draft/review calls plus strict Pydantic validation; the minimal doctor capability check uses `json_object`. MedMO required an explicit opening-brace instruction, and Qwen structured review disables template reasoning to bound output. Tool calling is not assumed. Mock mode requires `INFERENCE_MODE=MOCK`, uses a separate provider, and labels outputs. It never activates because real inference failed. Fault profiles are rejected in REAL mode and accepted only for loopback MOCK demonstration requests. Use `./scripts/mock_guide.sh` for the isolated mock runtime; it cannot silently replace the REAL provider.
