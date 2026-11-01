---
name: asking
description: "How to put a technical decision to the developer in Structured Vibe Code: show the relevant code or state, lay out concrete options with before/after, give a recommendation with its reason, and only then ask, with clickable choices. Use every time the developer must decide something: approach, naming, data shape, library, scope, whether to commit. Replaces bare questions and replaces the host's default question tool when a richer rendering is available."
---

# Asking

A question without context moves work from you to the developer. The developer should be able to decide by looking, not by reconstructing what you saw. This skill defines the only acceptable shape for a decision request.

## The four parts, in this order

1. **What is there now.** The code, config, schema, or state the decision touches. Quote the actual lines with `path:line`, trimmed to what matters. If nothing exists yet, show the nearest neighbor (the sibling module, the existing pattern you would follow).
2. **The options.** Two to four, never one. Each option gets a short name, a before/after (a diff, a code block pair, or a table when the change is structural), and the consequence that distinguishes it from the others: what it costs, what it blocks, what it leaves open. Include "do nothing / defer" when that is a real choice.
3. **Your recommendation and why.** One option, one paragraph. Say what would make you change your mind.
4. **The question.** One sentence, answerable by picking an option. If two independent decisions are needed, ask two questions in the same round rather than serializing turns.

Steps 1 to 3 are text the developer reads. Step 4 is the interactive part. Never send step 4 alone.

## Rendering, best available first

Check which of these the session has, in this order, and use the first one that exists.

### A. HTML widget (`show_widget` or an equivalent inline-render tool)

Render steps 2 to 4 as one self-contained HTML widget: one card per option, side by side, each with the option name, the before/after block, the one-line consequence, and a button. The recommended card is visually marked. Buttons call `sendPrompt("Option B: <option name>")` so the developer clicks and the conversation continues with that choice. Keep step 1 (current code) in the message text above the widget; it must survive even if the widget fails to render.

Use the widget when options differ in code shape, flow, or structure; a diagram of two flows side by side beats two paragraphs. Keep it under roughly 120 lines of HTML; this is a decision aid, not a product.

### B. Native question tool with previews (`AskUserQuestion` or equivalent)

One question per decision, options labeled by name, recommended option first with "(recommended)" in the label, each option's `description` holding the consequence, and the before/after in the option `preview` when the tool supports one. Steps 1 and 3 go in the message text before the tool call.

### C. Plain text

Numbered options, each with its before/after in a fenced block, recommendation marked with `→`, then the question. End the message there; do not continue working.

## Rules

- Never ask about something you can find in the repository. Look first.
- Never ask the developer to choose between options you have not actually compared. If you have not read the alternative, you have no option to offer.
- Never ask more than one round for the same decision. Gather every open sub-question whose prerequisites are settled and ask them together.
- Never decide by silence. No answer means no decision; stop and wait.
- Scope changes are decisions. Discovering that the slice is bigger than planned triggers this skill, not an expanded diff.
- Commit, push, delete, publish, migrate, and anything irreversible always go through this skill, in full prose, with the exact command shown.

## Example (plain-text rendering)

> **Now** (`server.py:23`):
> ```python
> DB_PATH = Path(os.environ.get("LAR_DB", BASE / "data" / "lar.db"))
> ```
> **Options**
> 1. **Keep env var, add CLI flag** — `--db` overrides `LAR_DB`. Two knobs, both documented.
> 2. **Config file** — `config.toml` next to the binary. Adds a parse step and a new file to ship.
> 3. **Defer** — leave as is; revisit when a second setting appears.
>
> → **1.** Smallest change, matches how the server is already started. I would switch to 2 if a third setting showed up.
>
> Which one?
