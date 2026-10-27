.PHONY: bootstrap doctor fixtures test test-real test-browser dev production create-doctor demo-mock demo-real evidence verify-evidence evidence-v2 verify-evidence-v2 clean-var static frontend-build
bootstrap:
	./scripts/bootstrap.sh
doctor:
	./scripts/doctor.sh
fixtures:
	uv run python scripts/generate_fixtures.py
static:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src
test: static
	uv run pytest -m "not real"
test-real:
	RUN_REAL_TESTS=1 INFERENCE_MODE=REAL uv run pytest -m real
test-browser: frontend-build
	uv run python scripts/verify_console_browser.py
dev:
	./scripts/dev.sh
production: frontend-build
	./scripts/production.sh
create-doctor:
	./scripts/create_doctor.sh
frontend-build:
	cd frontend && npm run build
demo-mock:
	INFERENCE_MODE=MOCK uv run python scripts/run_test_scenarios.py
demo-real:
	INFERENCE_MODE=REAL uv run python scripts/run_real_demo.py
evidence:
	uv run python scripts/capture_showcase_evidence.py
verify-evidence:
	uv run python scripts/build_v3_evidence.py
evidence-v2: evidence
verify-evidence-v2: verify-evidence
clean-var:
	uv run python -c 'import shutil; shutil.rmtree("var", ignore_errors=True)'
