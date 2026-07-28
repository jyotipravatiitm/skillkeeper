# Contributing to Skillkeeper

Thank you for helping make Agent Skills more observable, testable, and reversible.

## High-value contributions

- sanitized replay fixtures based on real failures;
- deterministic command, file, or artifact verifiers;
- skill-root detectors;
- runtime event adapters;
- clearer diagnostics and privacy controls;
- documentation that shortens install-to-first-value time.

Please open an issue before starting a large runtime or optimizer adapter so the evidence schema and privacy boundary can be agreed first.

## Development setup

```bash
git clone https://github.com/jyotipravatiitm/skillkeeper.git
cd skillkeeper
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

The v0 package intentionally has no runtime dependencies.

## Pull requests

1. Create a focused branch.
2. Add or update tests for behavioral changes.
3. Run the complete unittest suite.
4. Document new commands, schemas, and privacy implications.
5. Keep unrelated refactors out of the same pull request.

For adapters, include a minimal sanitized fixture and document which fields are stable, inferred, or runtime-version-specific.

## Design principles

- Evidence before claims.
- Local-first by default.
- Open Agent Skills compatibility.
- Candidates before mutation.
- Explicit promotion and immediate rollback.
- Confidence labels for inferred attribution.
