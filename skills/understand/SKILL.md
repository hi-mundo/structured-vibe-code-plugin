---
name: understand
description: "Map a repository before changing it: what it is, how it started, how it became what it is, and where it is heading. Reads git history in chronological chunks instead of the whole log, writes .vibecoding/understanding.md and refreshes STRUCTURE.md. Use for /vibecode understand, when joining an unfamiliar codebase, when STRUCTURE.md is missing or stale, or before any slice that touches a module you have not read."
---

# Understand

You help better when you know why the code looks the way it does. A repository's history explains more than its current tree: what was tried, what was torn out, which parts were written in a hurry, where the author is heading. This skill reads that history in chunks so a long log stays readable.

## Procedure

1. **Inventory the present.** Read `README`, `AGENTS.md`/`CLAUDE.md`, manifests, entry points, directory layout, test setup. Run `python3 <plugin>/scripts/review_preflight.py --repo . --mode deep` for the deterministic inventory. Note what the repository says about itself versus what the tree shows.
2. **Chunk the history.** Run `python3 <plugin>/scripts/history_chunks.py --repo . --chunks 6`. Exit 1 means fewer than 3 commits: skip to step 5 with "history too short". The JSON gives, per chunk: date span, commit count, authors, `top_paths` by churn, `top_dirs`, `new_areas` (paths seen for the first time), and sample subjects.
3. **Read each chunk, in order.** For every chunk: `git diff --stat <range.diff>`, then `git show --stat` or `git show -- <path>` on the two or three paths that explain that chunk's `new_areas` or largest churn. Write one paragraph per chunk before moving to the next: what was being built, what was removed, what changed direction. Keep the diffs you open proportional; you are reading for narrative, not reviewing.
4. **Find the turning points.** Across the paragraphs, mark the commits where the project changed what it was: a rename, a rewrite, a dropped dependency, a new entry point, a pivot in the README. Usually two to four.
5. **Write `.vibecoding/understanding.md`** with this shape:

   ```markdown
   # Understanding: <repo name>
   Generated: <ISO date>  Base commit: <HEAD>  Commits read: <n> in <k> chunks

   ## What it is now
   One paragraph. Purpose, users, main entry points, where the weight of the code sits.

   ## How it started
   First chunk(s): the original idea, the first shape of the tree.

   ## How it became this
   One short section per turning point: what changed, which commits, what it replaced.

   ## Where it is going
   Last chunk plus open TODOs, stubs, unfinished branches, backlog hints in commits.

   ## Load-bearing parts
   Paths whose churn or centrality means a slice there needs extra care.

   ## Questions for the developer
   Things the history does not settle. Ask these through the `asking` skill, not here.
   ```
6. **Refresh `STRUCTURE.md`.** Fill or update its sections from what you now know, set `Base commit:` to the current HEAD so `protector_preflight.py` stops reporting `MODEL002_STRUCTURE_STALE`. Show the developer the diff of `STRUCTURE.md` before writing it when the file already had content.
7. **Report.** Give the developer the "What it is now" and "Where it is going" paragraphs in the message, the path to the full file, and the questions from the last section as a decision round (`asking` skill). Then offer the next step: enable active mode, pick a slice, or dig into one load-bearing part.

## Scale

- Under 50 commits: 3 chunks, read most diffs.
- 50 to 1000 commits: 6 chunks, `--stat` plus a few `git show` per chunk.
- Over 1000: 8 to 10 chunks, `--stat` only unless a chunk is a turning point. Pass `--max-commits` to bound time.

Prefer finishing a shallow pass over the whole history to a deep pass over a third of it; the developer can ask for depth on a chunk.

## What this skill does not do

It does not judge code quality, propose refactors, or edit anything other than `.vibecoding/understanding.md` and `STRUCTURE.md`. Observations that look like work go to `.vibecoding/execution-backlog.json` as candidates, marked `source: understand`.
