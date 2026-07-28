# Security policy

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository:

<https://github.com/jyotipravatiitm/skillkeeper/security/advisories/new>

Do not include secrets, private transcripts, or customer data in a public issue.

## Current security boundary

Skillkeeper v0 reads local skill packages and replay fixtures and writes its SQLite database, candidates, and backups beneath the configured state directory.

- Keep the state directory outside scanned skill roots.
- Treat third-party skills, scripts, and references as untrusted content.
- Review candidate diffs before promotion.
- Do not run untrusted skill scripts without an appropriate sandbox.
- Current package validation is not malware detection.

Future trace adapters must default to metadata-only analysis, avoid storing raw transcripts, and require explicit consent before provider-assisted semantic analysis.
