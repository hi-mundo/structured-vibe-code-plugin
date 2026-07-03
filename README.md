# Codex OpenAI Local Wrapper

Run `codex app-server` behind a small local HTTP API that looks like the OpenAI API.

This project is intentionally local-first:

- binds to `127.0.0.1` by default;
- refuses non-loopback HTTP hosts;
- uses Node.js built-ins only;
- generates Codex app-server protocol files from your installed `codex` binary;
- shows live request, warning, and error logs in an interactive CLI.

## What You Get

- `POST /v1/responses`
- `POST /v1/chat/completions`
- `GET /health`
- interactive terminal UI with hotkeys
- daemon mode for scripts and automation
- optional local bearer-token auth
- per-request `cwd` override for Codex turns

This is not an official OpenAI API server. It is a local adapter for development and automation around `codex app-server`.

## Requirements

- Node.js 22+
- `codex` available on `PATH`

## Quickstart

Generate the Codex app-server protocol files:

```sh
npm run setup
```

Start Codex app-server locally:

```sh
codex app-server --listen ws://127.0.0.1:8080
```

In another terminal, start the HTTP wrapper in interactive CLI mode:

```sh
npm run dev
```

Health check:

```sh
curl http://127.0.0.1:3000/health
```

Send a Responses-style request:

```sh
curl -sS http://127.0.0.1:3000/v1/responses \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "input": "Inspect this project and summarize what it does."
  }'
```

## CLI Modes

### Interactive TUI

```sh
npm run start
```

The terminal shows live requests, warnings, errors, and a bottom shortcut bar:

- `r`: restart HTTP server
- `t`: regenerate local API token
- `c`: change runtime config
- `q`: quit

### Daemon Mode

Start without the TUI:

```sh
node src/server.mjs -d
```

Start without the TUI and require a local bearer token:

```sh
node src/server.mjs -d ai
```

Then call routes with:

```sh
Authorization: Bearer ai
```

## Routes

### `POST /v1/responses`

```sh
curl -sS http://127.0.0.1:3000/v1/responses \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "input": "Say hello from Codex."
  }'
```

With auth enabled:

```sh
curl -sS http://127.0.0.1:3000/v1/responses \
  -H 'authorization: Bearer ai' \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "input": "Say hello from Codex."
  }'
```

### `POST /v1/chat/completions`

```sh
curl -sS http://127.0.0.1:3000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "messages": [
      { "role": "user", "content": "Say hello from Codex." }
    ]
  }'
```

## Configuration

Environment variables:

- `HOST`: HTTP bind host. Defaults to `127.0.0.1`. Non-loopback hosts are refused.
- `PORT`: HTTP port. Defaults to `3000`.
- `CODEX_APP_SERVER_URL`: Codex websocket URL. Defaults to `ws://127.0.0.1:8080`.
- `CODEX_APP_SERVER_TOKEN`: optional bearer token for a Codex app-server started with websocket auth.
- `CODEX_CWD`: default working directory passed to Codex turns. Defaults to this wrapper directory.
- `CODEX_TIMEOUT_MS`: Codex turn timeout. Defaults to `120000`.
- `LOCAL_API_KEY`: optional local bearer token required by wrapper routes.

The shortcut `t` regenerates `LOCAL_API_KEY` in memory for the running CLI session.

Per-request cwd override:

```json
{
  "model": "codex",
  "input": "List the files in this project.",
  "codex": {
    "cwd": "/absolute/path/to/project"
  }
}
```

## How It Works

The wrapper accepts OpenAI-shaped HTTP requests, translates them into Codex app-server websocket calls, waits for Codex turn completion, and maps the assistant text back into an OpenAI-shaped response.

Internal Codex flow:

```text
HTTP request
  -> websocket connect
  -> initialize
  -> thread/start
  -> turn/start
  -> collect item/agentMessage/delta
  -> wait for turn/completed
  -> HTTP response
```

## Regenerate Protocol Files

The generated files live under `generated/codex-app-server/` and are ignored by git. Regenerate them whenever your installed Codex version changes:

```sh
npm run setup
```

## Current Scope

Implemented:

- `GET /health`
- `POST /v1/responses`
- `POST /v1/chat/completions`
- local-only HTTP bind guard
- explicit errors for unsupported streaming
- protocol file generation through `codex app-server generate-ts`

Not implemented yet:

- `stream: true` SSE compatibility
- tools/function calling
- file inputs
- persistent conversation IDs
- usage/token accounting

## Troubleshooting

### `listen EPERM` in sandboxed environments

Some managed sandboxes block local TCP listeners. Run the wrapper from a normal terminal:

```sh
node src/server.mjs -d ai
```

### `Failed to connect to codex app-server`

Start Codex app-server first:

```sh
codex app-server --listen ws://127.0.0.1:8080
```

If you changed the websocket URL:

```sh
CODEX_APP_SERVER_URL=ws://127.0.0.1:9090 npm run start
```

### `401 Invalid LOCAL_API_KEY bearer token`

Pass the bearer token configured by `LOCAL_API_KEY`, the daemon argument, or the TUI `t` shortcut:

```sh
curl -H 'authorization: Bearer ai' http://127.0.0.1:3000/health
```
