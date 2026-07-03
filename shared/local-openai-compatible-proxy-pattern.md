# Local OpenAI-Compatible Proxy Pattern

Use this pattern when a local agent speaks one protocol but a client expects an
OpenAI-style HTTP API.

## Shape

```text
OpenAI-shaped HTTP request
  -> validate JSON body
  -> convert input/messages into agent prompt
  -> call local agent protocol
  -> collect assistant output
  -> return OpenAI-shaped JSON
```

## Routes

The smallest useful surface is:

- `GET /health`
- `POST /v1/responses`
- `POST /v1/chat/completions`

Return explicit errors for unsupported features:

- `stream: true`
- tool calls
- file inputs
- remote bind hosts

## Security Boundary

Default to:

```text
127.0.0.1
```

Avoid `0.0.0.0` unless the prompt also adds authentication and names the risk.
Local bridge prompts should not commit tokens, generated certs, or temporary
scripts.

## Observability

Log:

- request method and path;
- request completion time;
- active request count;
- agent protocol warnings;
- agent protocol failures;
- cleanup/shutdown events.

Never return a successful OpenAI-shaped response when the underlying agent call
failed.
