# Skillkeeper roadmap

Skillkeeper is being built in three layers. Each layer must remain useful without requiring the next one.

## Available in v0.1

- Agent Skills folder scanning and package checks
- local SQLite inventory and audit events
- deterministic replay cases
- explainable package, coverage, and replay health
- bounded candidate generation in staging
- training and held-out promotion gates
- readable diffs and hash tamper checks
- explicit promotion, backup, and rollback
- presentation before/after demo with receipts

## Next: first 10-minute Quality Pulse

- `skillkeeper init` with runtime, skill-root, and trace discovery
- metadata-only privacy mode by default
- `skillkeeper doctor` with actionable environment fixes
- human-readable terminal tables while retaining JSON output
- trace adapters for Claude Code and Hermes
- experimental, versioned Codex trace importer
- drift, usage, tool-reliability, duration, and confidence views

## Then: corrections become tests

- evidence view for one agent or skill
- local correction and retry detection with user confirmation
- `case create --from-run RUN_ID`
- role-specific outcome templates for content, research, sales, support, finance, operations, and engineering
- artifact and command verifiers

## Later: closed improvement loop

- behavioral replay through supported runtimes
- optional SkillOpt candidate-generation adapter
- cross-skill regression selection
- canary comparisons between skill versions
- signed evidence bundles and team review policy

## Non-goals

- fine-tuning model weights
- another public skill marketplace
- silently installing untrusted skills
- uploading raw personal transcripts by default
- claiming model-judge scores make autonomous mutation safe
- auto-promoting destructive or externally visible skills

Roadmap items are promoted into release milestones only after their data boundary, verifier contract, and user-facing outcome are clear.
