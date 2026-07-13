# Awesome VibeCoding Plugins

Codex plugin source for review, development, debugging, and observable local workflows.

The repository is organized as a repo-backed marketplace. Each distributable capability lives under `plugins/<plugin-name>/` with its own manifest, skills, references, and deterministic runtime scripts when needed.

## Plugins

### Intent-to-Behavior Review

[Open the plugin source](plugins/intent-to-behavior-review/)

- Reconstructs what an application or feature should do before treating its current implementation as correct.
- Supports deep repository, scoped feature, and branch/commit comparison reviews.
- Inspects at least three meaningful revisions to model behavioral evolution.
- Finds semantic, functional, domain, integration, state, and observability defects—including successful executions that fail their purpose.
- Includes deterministic Python preflight, direct-import mimic, and report-validation helpers.
- Uses published IEEE, ACM, Wiley, Springer Nature, and IBM Research foundations.

## Install as a Codex plugin source

```bash
git clone https://github.com/hi-mundo/awesome-vibecoding-plugins.git
codex plugin marketplace add /absolute/path/to/awesome-vibecoding-plugins
codex plugin add intent-to-behavior-review@awesome-vibecoding-plugins
```

The marketplace identifier is `awesome-vibecoding-plugins`, as declared in `.agents/plugins/marketplace.json`.

## Repository shape

```text
.agents/plugins/marketplace.json
plugins/
  intent-to-behavior-review/
    .codex-plugin/plugin.json
    skills/
      intent-to-behavior-review/
        SKILL.md
        agents/openai.yaml
        references/
    scripts/
codex/   # legacy prompt/reference material
shared/  # legacy shared patterns
warp/    # legacy Warp notes
```

New distributable work belongs under `plugins/`. The existing `codex/`, `shared/`, and `warp/` documents are retained as reference material; they are not advertised as installable plugins.

## Plugin quality bar

- State the behavior and boundaries the plugin owns.
- Keep failure states visible; never fabricate success.
- Prefer local, deterministic helpers for repeated mechanical work.
- Keep product and domain decisions with the user.
- Include focused validation for scripts and manifests.
- Document external references and known methodological limits.

## License

MIT.
