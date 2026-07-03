# Codex App-Server Websocket Notes

`codex app-server` exposes a websocket interface. The local proxy prompt in
this repo uses that interface to translate OpenAI-shaped HTTP requests into
Codex turns.

## Loopback First

For local development, prefer:

```sh
codex app-server --listen ws://127.0.0.1:8080
```

Do not bind to `0.0.0.0` unless you also configure websocket auth. Codex
correctly refuses a non-loopback websocket listener without auth.

## Auth Shape

For non-loopback use, Codex requires websocket auth such as:

```sh
codex app-server \
  --listen ws://0.0.0.0:8080 \
  --ws-auth capability-token \
  --ws-token-sha256 <64-character-sha256-hex-digest>
```

For local-only prompt recipes, keep the listener on `127.0.0.1` and avoid the
extra auth path unless there is a clear reason.

## Why Not Only Bash And nc

`nc` can send and receive plain TCP bytes. That works for simple HTTP checks:

```sh
printf 'GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n' | nc 127.0.0.1 3000
```

WebSocket is different. After the HTTP upgrade handshake, messages are encoded
as websocket frames. A correct bridge needs a websocket client implementation.
The prompt uses Node.js built-ins for that reason.

## Expected Turn Flow

The practical lifecycle is:

```text
websocket connect
  -> initialize
  -> initialized
  -> thread/start
  -> turn/start
  -> collect assistant message deltas
  -> wait for turn completion or failure
  -> close websocket
```

Keep failures visible. If the protocol shape changes, the bridge should return
an explicit error rather than fake an empty successful response.
