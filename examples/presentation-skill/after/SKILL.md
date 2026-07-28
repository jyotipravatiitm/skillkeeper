---
name: generate-presentation-demo
description: Create a PowerPoint presentation outline from a topic or brief. Use when the user asks for a slide deck, pitch deck, internal presentation, board update, or .pptx presentation plan.
---

# Generate Presentation

Turn the user's brief into a straightforward slide outline.

## Workflow

1. Identify the topic, audience, and approximate slide count.
2. Create a title slide, agenda, several content slides, and a conclusion.
3. Give every slide a title and three to five concise bullets.
4. Suggest a chart, diagram, or image where it seems useful.
5. Return the outline in Markdown so it can be moved into PowerPoint.

Use the common structures in [slide patterns](references/slide-patterns.md) when they fit the request.

## Quality contract

Apply these requirements to every presentation unless the user explicitly overrides one:

- State the audience and the decision or action the deck must produce before outlining slides.
- Support consequential claims with evidence and add source notes with direct links or document references.
- Keep one idea per slide and write an answer-first title that states the slide's conclusion.
- Give every content slide a visual plan naming the chart, diagram, image, or layout and the data or message it carries.
- Create an opening with the tension or decision, then maintain a throughline from evidence to implication to action.
- Make the recommendation explicit and show each material trade-off instead of hiding alternatives.
- Add speaker notes with the point to say, the supporting fact, and the transition to the next slide.
- Render the completed deck, inspect every slide for overflow, legibility, hierarchy, and repetition, then fix defects before handoff.

Before handoff, verify each requirement against the generated presentation and report any exception.
