# Presentation skill: before and after

This demo shows the full v0 Skillkeeper lifecycle on a deliberately weak presentation skill.

## Artifacts

| Version | PDF | Editable PowerPoint | Contact sheet |
|---|---|---|---|
| Before | [Open PDF](decks/mcp-like-five-before.pdf) | [Open PPTX](decks/mcp-like-five-before.pptx) | [Open image](before.png) |
| After | [Open PDF](decks/mcp-like-five-after.pdf) | [Open PPTX](decks/mcp-like-five-after.pptx) | [Open image](after.png) |

## Scenario

The starting `generate-presentation-demo` skill produced a title, agenda, bullet slides, suggested visuals, and a conclusion. It lacked explicit controls for evidence, decision focus, narrative, source notes, slide-level visual plans, speaker notes, and rendered visual QA.

Skillkeeper ran two training replays, generated a bounded quality-contract candidate, and evaluated that candidate on an unseen board-update replay.

## Evaluation result

| Measure | Before | Candidate / after |
|---|---:|---:|
| Overall health | 50/100 | 100/100 |
| Training replay | 0/8 | 8/8 |
| Held-out board replay | 0/4 | 4/4 |
| Skill package issues | 0 | 0 |

The live skill changed only after the candidate was inspected and explicitly promoted. The prior version was retained for rollback.

## Receipts

- [`candidate-v2.diff`](receipts/candidate-v2.diff) — exact bounded change
- [`candidate-v2.json`](receipts/candidate-v2.json) — training and held-out gate scores
- [`promotion-v2.json`](receipts/promotion-v2.json) — promotion record
- [`health-before-v2.json`](receipts/health-before-v2.json) — baseline health
- [`health-after-v2.json`](receipts/health-after-v2.json) — post-promotion health
- [`events-v2.json`](receipts/events-v2.json) — inventory, candidate, and promotion audit events

## Important boundary

This v0 demonstrates deterministic **skill-contract improvement**. It does not claim that phrase matching judged the visual quality of these slides. The decks are a human-inspectable illustration of why a stronger skill contract matters.

The next artifact evaluator should generate the deck, render it, and measure overflow, readability, claim traceability, narrative coherence, and user correction rate while preserving the same staging, gate, promotion, and rollback lifecycle.
