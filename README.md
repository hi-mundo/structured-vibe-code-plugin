# Codex OpenAI Local Wrapper

Run `codex app-server` behind a small local HTTP API that looks like the OpenAI API.

This project is intentionally local-first:

- binds to `127.0.0.1` by default;
- serves clients through the local-friendly host `codex.local`;
- serves HTTPS by default with an auto-generated local certificate;
- refuses non-loopback HTTP hosts;
- uses Node.js built-ins only;
- starts `codex app-server` for you on loopback;
- generates Codex app-server protocol files from your installed `codex` binary when needed;
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

Map the local domain once:

```sh
sudo sh -c 'grep -q "codex.local" /etc/hosts || echo "127.0.0.1 codex.local" >> /etc/hosts'
```

Start the wrapper:

```sh
npm run start
```

That is enough for the normal path. On boot, the wrapper:

- checks whether generated Codex protocol files already exist;
- generates them if they are missing;
- starts a managed local `codex app-server`;
- creates a self-signed local TLS certificate if needed;
- starts the OpenAI-style HTTP API.

Health check:

```sh
curl -k https://codex.local:3000/health
```

Send a Responses-style request:

```sh
curl -k -sS https://codex.local:3000/v1/responses \
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
curl -k -sS https://codex.local:3000/v1/responses \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "input": "Say hello from Codex."
  }'
```

With auth enabled:

```sh
curl -k -sS https://codex.local:3000/v1/responses \
  -H 'authorization: Bearer ai' \
  -H 'content-type: application/json' \
  -d '{
    "model": "codex",
    "input": "Say hello from Codex."
  }'
```

### `POST /v1/chat/completions`

```sh
curl -k -sS https://codex.local:3000/v1/chat/completions \
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

- `BIND_HOST`: HTTP bind host. Defaults to `127.0.0.1`. Non-loopback hosts are refused.
- `PUBLIC_HOST`: advertised host used in docs, TUI and health responses. Defaults to `codex.local`.
- `HOST`: backwards-compatible alias for `BIND_HOST`.
- `PORT`: HTTP port. Defaults to `3000`.
- `TLS_ENABLED`: set to `false` to use plain HTTP. Defaults to HTTPS.
- `TLS_CERT_DIR`: local certificate directory. Defaults to `.local/certs`.
- `CODEX_APP_SERVER_PORT`: managed Codex app-server port. Defaults to `8080`.
- `CODEX_APP_SERVER_TOKEN`: optional bearer token for a Codex app-server started with websocket auth.
- `CODEX_CWD`: default working directory passed to Codex turns. Defaults to this wrapper directory.
- `CODEX_TIMEOUT_MS`: Codex turn timeout. Defaults to `120000`.
- `LOCAL_API_KEY`: optional local bearer token required by wrapper routes.

The shortcut `t` regenerates `LOCAL_API_KEY` in memory for the running CLI session.

Advanced: set `CODEX_APP_SERVER_URL` only if you intentionally want to connect to an already-running external app-server instead of letting the wrapper manage it.

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
HTTPS request
  -> websocket connect
  -> initialize
  -> thread/start
  -> turn/start
  -> collect item/agentMessage/delta
  -> wait for turn/completed
  -> HTTP response
```

## Protocol Files

The generated files live under `generated/codex-app-server/` and are ignored by git. The wrapper creates them automatically when they are missing.

You can regenerate them manually after upgrading Codex:

```sh
npm run setup
```

## Local TLS

The wrapper generates a self-signed certificate for:

- `codex.local`
- `localhost`
- `127.0.0.1`
- `::1`

For quick local testing, use `curl -k`.

```sh
curl -k https://codex.local:3000/health
```

For clients that require trusted TLS, import `.local/certs/codex.local.crt` into your local trust store, or run with plain HTTP:

```sh
TLS_ENABLED=false npm run start
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

### Managed Codex app-server cannot start

The wrapper starts Codex on `127.0.0.1:8080` by default. If that port is already busy:

```sh
CODEX_APP_SERVER_PORT=9090 npm run start
```

### `401 Invalid LOCAL_API_KEY bearer token`

Pass the bearer token configured by `LOCAL_API_KEY`, the daemon argument, or the TUI `t` shortcut:

```sh
curl -k -H 'authorization: Bearer ai' https://127.0.0.1:3000/health
```

You can also use:

```sh
curl -k -H 'authorization: Bearer ai' https://codex.local:3000/health
```
