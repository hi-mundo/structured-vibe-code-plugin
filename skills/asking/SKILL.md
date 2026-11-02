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

The tool call is the *last* thing in the turn, never the only thing. Fill it like this:

- `question`: the decision in one sentence, ending in `?`. Not "Proceed?" but "Which storage for the slice state?".
- `options[].label`: the option's **name**, 1 to 5 words. Forbidden labels: `Yes`, `No`, `OK`, `Proceed`, `Continue`, `Do it`, `Fix`, `Do X first`. If you cannot name the option, you have not designed it.
- `options[].description`: mandatory, 1 to 2 sentences: what changes, what it costs or blocks. Not a restatement of the label.
- `options[].preview`: the before/after or diff for that option whenever code or config is involved. The developer should be able to pick by looking at the previews alone.
- Recommended option first, `(recommended)` in its label.
- Steps 1 and 3 (current code, recommendation with reason) go in the message **above** the tool call. A tool call with an empty message above it is a violation.

Bad, the kind this skill exists to prevent:

```json
{"question": "Proceed?", "options": [{"label": "Yes", "description": "Go ahead"}, {"label": "Run understand first", "description": "Run it first"}]}
```

Good:

```json
{"question": "What should happen with the init files before the first slice?",
 "options": [
  {"label": "Commit scaffolding (recommended)", "description": "One commit with .gitignore, STRUCTURE.md skeleton and the empty decision log. Clears PRE001 now; STRUCTURE.md gets filled in a later commit.", "preview": "chore: add Structured Vibe Code scaffolding\n\n .gitignore | 3 +\n STRUCTURE.md | 26 +\n .decisions.jsonl | 0"},
  {"label": "Understand, then commit", "description": "Runs /vibecode understand first so STRUCTURE.md is filled in the same commit. Costs one more pass over 4 commits of history; keeps the log at one commit instead of two."},
  {"label": "Keep worktree dirty", "description": "Nothing committed. Every slice diff from now on also shows these three files, and preflight keeps reporting PRE001."}
 ]}
```

### C. Plain text

Numbered options, each with its before/after in a fenced block, recommendation marked with `→`, then the question. End the message there; do not continue working.

## Rules

- A button is a decision, not an acknowledgement. If the only honest options are "yes" and "no", there is no decision to render: state what you will do and why, and ask for the go in one plain sentence instead.
- Never ask about something you can find in the repository. Look first.
- Never ask the developer to choose between options you have not actually compared. If you have not read the alternative, you have no option to offer.
- Never ask more than one round for the same decision. Gather every open sub-question whose prerequisites are settled and ask them together.
- Never decide by silence. No answer means no decision; stop and wait.
- Scope changes are decisions. Discovering that the slice is bigger than planned triggers this skill, not an expanded diff.
- Commit, push, delete, publish, migrate, and anything irreversible always go through this skill, in full prose, with the exact command shown.
- Terse voice (`/vibecode terse`) never applies to steps 2 to 4. Options, descriptions, previews and the question are full sentences, so the answer comes back right the first time.

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
