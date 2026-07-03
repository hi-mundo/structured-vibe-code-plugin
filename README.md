# Awesome Agent Prompts

Reusable prompts, skills, and local recipes for developer agents.

This repository is a curated place for prompts that make agents do real work:
start local services, bridge protocols, inspect projects, write docs, debug
failures, and keep the workflow observable.

The prompts are written to be copied into an agent session. They should be
self-contained, local-first when possible, and explicit about setup,
validation, logs, cleanup, and known limits.

## Catalog

### Codex

- [OpenAI-compatible local proxy prompt](codex/openai-compatible-local-proxy.md)
  - Starts `codex app-server` locally.
  - Creates a temporary mini proxy from OpenAI-style HTTP routes to the Codex
    websocket protocol.
  - Exposes `GET /health`, `POST /v1/responses`, and
    `POST /v1/chat/completions`.
  - Keeps the bind host on `127.0.0.1`.

- [Codex app-server websocket notes](codex/app-server-websocket-notes.md)
  - Practical notes for the Codex app-server websocket lifecycle.
  - Auth and loopback guidance.
  - Why raw `nc` is useful for HTTP checks but not enough for websocket frames.

### Warp

- [Using local OpenAI-compatible providers from Warp](warp/custom-openai-provider-local.md)
  - Notes for local-only endpoints.
  - Why `codex.local` can fail when a client resolves DNS outside your machine.
  - Safer local alternatives.

### Shared Patterns

- [Local OpenAI-compatible proxy pattern](shared/local-openai-compatible-proxy-pattern.md)
  - A reusable pattern for converting OpenAI-shaped HTTP requests into another
    local agent protocol.

- [Prompt template](shared/prompt-template.md)
  - A small template for adding new prompts to this repo.

## Repository Shape

```text
codex/
  openai-compatible-local-proxy.md
  app-server-websocket-notes.md
warp/
  custom-openai-provider-local.md
shared/
  local-openai-compatible-proxy-pattern.md
  prompt-template.md
```

Future tools can get their own folder, for example `cursor/`, `claude-code/`,
`aider/`, or `opencode/`.

## What Makes A Prompt Belong Here

A good prompt in this repository should include:

- the goal it accomplishes;
- assumptions and required local tools;
- exact commands or scripts to create;
- security boundaries, especially bind hosts and tokens;
- logs or checks that make failures visible;
- cleanup instructions;
- at least one validation command.

## Local-First Bias

Most recipes here prefer local loopback services:

- bind to `127.0.0.1` by default;
- avoid exposing ports publicly;
- avoid committing generated credentials or certificates;
- make warnings and failures visible in the terminal;
- leave generated scripts in temporary directories unless the prompt says
  otherwise.

## License

MIT. Use the prompts, adapt them, and keep security boundaries explicit.
