# Repair Actions Checklist

This file enumerates concrete steps to address common failures identified by the Gate Runner or the E2E test suite.

## 1. Lint Issues (Gate A)
- Run `flake8 .` locally.
- Apply `black .` for formatting.
- Commit the changes and re‑run the pipeline.

## 2. Test Coverage Drops (Gate B)
- Identify uncovered modules via `coverage html`.
- Write unit tests targeting uncovered lines.
- Ensure total coverage >= 80%.

## 3. Security Vulnerabilities (Gate C)
- Run `pip-audit` to list vulnerable dependencies.
- Upgrade packages with `pip install --upgrade <pkg>`.
- If CVEs persist, evaluate alternative libraries.

## 4. E2E Test Failures
- Re‑run the failing test with `pytest -vv tests/e2e/<test_file>.py`.
- Capture logs and HTTP traces.
- Check environment configuration (e.g., database URLs, auth tokens).
- Update `tests/e2e/helpers.py` with missing mock data if needed.

## 5. Gate Runner Execution Errors
- Verify that `pipelines/gate-runner/gate_runner.py` is executable (`chmod +x`).
- Ensure all required Python packages are installed (`requirements.txt`).
- Run the script locally: `python -m pipelines.gate-runner.gate_runner`.

---
**Note**: After applying any repair action, commit the changes and push to the repository to trigger CI verification.
