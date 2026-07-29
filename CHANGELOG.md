# Changelog

All notable changes to Skillkeeper will be documented here.

## 0.1.2 — 2026-07-29

- Made `skillkeeper scan` discover skills recursively from the current project with no required path arguments.
- Excluded generated, dependency, virtual-environment, and version-control directories from automatic scans.
- Deduplicated skills when explicit scan roots overlap.
- Simplified the first-run documentation around the current-project workflow.

## 0.1.1 — 2026-07-29

- Added an npm launcher for `npx skillkeeper` and global npm installation.
- Added npm packaging and launcher verification to CI.
- Removed internal GTM and activation-planning documents from the user-facing repository.
- Focused the README on installation, first use, safety, and current capabilities.

## 0.1.0 — 2026-07-28

- Initial public release.
- Local Agent Skills inventory and package validation.
- Deterministic replay evaluation and explainable health.
- Bounded staged repair with training and held-out gates.
- Hash-checked promotion, backup, rollback, and audit events.
- Presentation before/after demo and evaluation receipts.
- Public roadmap and product boundaries.
