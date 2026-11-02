---
name: prior-art
description: "Never reinvent the wheel. Before building anything a repository does not yet have (module, dependency, integration, algorithm, tooling), find what already solves it: first inside the repository, then in two to four community or competitor projects. Each finding comes with source and license and becomes an option in the decision round. License gate: permissive code may be reused with its notice; copyleft, proprietary, unlicensed or share-alike code only informs the design. Use whenever a task says build, add, create, integrate or implement something new."
---

# Prior art

A module written from scratch is a decision, usually an expensive one. Someone has almost always solved the problem, often inside this very repository. This skill makes that search a required step and defines how its result reaches the developer: as options, with sources and licenses, never as a report on its own.

## Trigger

Run it when either holds:

- the slice would create a new file, package, service, or dependency, or
- the task verb is build / add / create / integrate / implement and its object does not appear in `STRUCTURE.md`.

Skip it when the slice only touches existing files and adds no dependency: bug fixes, renames, changes to a contract the repository already owns. When unsure, run it; it costs a few searches, a wrong "from scratch" costs a module.

Budget: six searches in total (repository and web together). When the budget is spent, stop and bring what you have; "found nothing comparable" after six honest searches is a valid result and is said as such.

## Step 1: the repository

Before any external search:

1. `grep` and `glob` for the concept, its synonyms and its usual symbol names: sibling modules, `utils`, `lib`, `vendor`, scripts, tests.
2. `STRUCTURE.md` and `.vibecoding/understanding.md`: an area that already owns the concern.
3. `.decisions.jsonl`: a previous decision that already picked a library or an approach. A recorded choice is not reopened silently; it is shown as the current state.
4. Dependency manifests and lockfiles (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`): something already installed may expose what is needed.

A hit here is option one in the decision round: reuse or extend, with the exact `path:line`.

## Step 2: the community

Two to four projects, in this order, one paragraph each, stop when the picture is clear:

1. The specification or reference implementation, when one exists (RFC, W3C, the language's own standard library).
2. What the framework or ecosystem documentation recommends for this problem.
3. The most adopted library of the ecosystem for it (downloads, dependents, release cadence).
4. One direct competitor of the product being built, for product-level features.

Read source and tests, not marketing pages. For each project capture:

| Field | Capture |
|---|---|
| project | name and URL (repository or documentation) |
| license | SPDX identifier; `none` when no license file exists |
| mechanism | data shape, flow, the trade-off it accepted, in two or three sentences |
| cost | size, transitive dependencies, maintenance state (last release, open issues), lock-in, platform limits |
| used_as | `dependency`, `code` (copy with attribution), or `pattern` (design only) |

## Step 3: the license gate

`used_as` follows from the license, not from convenience.

| License | Where to confirm it | Allowed |
|---|---|---|
| MIT, BSD-2/3, ISC, Apache-2.0, Unlicense, CC0, 0BSD | `LICENSE` file; `license` field in `package.json`, `pyproject.toml`, `Cargo.toml`; GitHub API `license.spdx_id` | `dependency`, `code` with the original notice kept and an entry in `THIRD_PARTY_NOTICES.md`, `pattern` |
| MPL-2.0, LGPL-2.1/3.0 | same | `dependency` without modifying it (LGPL: linked dynamically, not vendored), `pattern`; never paste its code |
| GPL, AGPL, SSPL, BUSL, Commons Clause, proprietary, source-available, `none` | same; `none` when no license file and no `license` field | `pattern` only: no code, no identifiers, no comments copied; write the implementation in the repository's own vocabulary |
| CC BY-SA (Stack Overflow answers, most wikis and blogs) | the site's footer or the post's license line | `pattern` only: share-alike would bind the repository |
| Dual-licensed | the project's `LICENSE*` files | pick the permissive branch and name it in the record |
| Unknown or contradictory | — | the strictest row until the developer rules otherwise |

Two more checks the developer needs from you:

- The repository's own license. A closed or permissive repository cannot take a GPL dependency; LGPL only as a dynamically linked dependency; AGPL never for anything served over a network. Say the pair ("ours MIT, theirs GPL-3.0") and let the developer decide.
- Documentation examples follow the documentation's license, which often differs from the code's.

## Step 4: into the decision round

Prior art does not get its own report; it becomes the options of the `asking` round, each option named by its origin:

- "Reuse `src/util/retry.py:12`" (found in step 1)
- "Adopt `tenacity` (Apache-2.0, dependency), as `httpx` and `prefect` do"
- "Own implementation following `resilience4j` (Apache-2.0, pattern): decorrelated jitter, circuit state per host"
- "Own implementation; `project K` (AGPL-3.0, pattern only) solves it with a sliding window, its code cannot be copied"

The recommendation names the finding it rests on and what would change it: the license changes, the dependency goes unmaintained, the internal utility turns out too narrow.

## Step 5: the record

The chosen option goes into `.decisions.jsonl` through `decision_log.py` with the findings attached, so a later `/vibecode understand` can read them:

```bash
python3 <plugin>/scripts/decision_log.py --file .decisions.jsonl \
  --domain retry --scope http --paths-json '["src/http/client.py"]' \
  --decision "adopt tenacity" --reason "..." --status accepted \
  --prior-art-json '[{"project":"tenacity","url":"https://github.com/jd/tenacity","license":"Apache-2.0","used_as":"dependency"},
                     {"project":"resilience4j","url":"https://github.com/resilience4j/resilience4j","license":"Apache-2.0","used_as":"pattern"},
                     {"project":"project K","license":"AGPL-3.0","used_as":"pattern"}]'
```

`used_as` accepts only `dependency`, `code`, `pattern`; anything else exits 11 (`DEC011`). If code was copied under a permissive license, the `THIRD_PARTY_NOTICES.md` entry lands in the same slice, not later.

## Never

- Install a dependency, vendor a file or copy a block before the developer picked the option.
- Present "write it from scratch" as the only option when step 1 or step 2 found anything.
- Hide a finding because its license is inconvenient; the developer sees it, labelled `pattern only`.

Related: `asking` (how the options are rendered), `vibecode` (where this fits in the loop), `understand` (where previous choices are recorded).
