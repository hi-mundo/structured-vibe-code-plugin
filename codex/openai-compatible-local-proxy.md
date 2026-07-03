# Codex OpenAI-Compatible Local Proxy

Copy this prompt into Codex when you want Codex itself to start a local
`codex app-server` and create a temporary OpenAI-style HTTP bridge.

This prompt intentionally creates a small local script at runtime instead of
requiring a reusable Node package. It uses Bash for orchestration and an inline
Node.js mini server for the websocket bridge because websocket frames are not
plain TCP text. `nc` is useful for simple HTTP readiness probes, but it is not a
correct websocket client by itself.

## Prompt

````text
You are running on my local machine. Create a temporary local OpenAI-compatible
HTTP proxy for Codex app-server.

Goal:
- Start `codex app-server` on loopback if it is not already reachable.
- Serve OpenAI-style local HTTP routes:
  - GET /health
  - POST /v1/responses
  - POST /v1/chat/completions
- Translate requests to the Codex app-server websocket protocol.
- Log every request, warning, and error to the terminal.
- Keep everything local-only.

Constraints:
- Bind HTTP only to 127.0.0.1.
- Do not expose 0.0.0.0.
- Do not require a permanent repository or npm package.
- Use only Node.js built-ins and the installed `codex` CLI.
- Prefer port 3000 for HTTP and 8080 for Codex app-server, but pick another
  free port if needed.
- If Node.js does not provide global WebSocket, stop and explain that Node 22+
  is required for this minimal no-dependency version.
- If `stream: true` is requested, return a clear 400 error saying streaming is
  not implemented by this mini proxy.
- On Ctrl-C, stop the managed app-server child process and the HTTP server.

Implementation steps:

1. Check prerequisites:
   - `command -v codex`
   - `node -e "console.log(process.version); if (!globalThis.WebSocket) process.exit(2)"`

2. Create a temporary script:

```sh
cat > /tmp/codex-openai-local-proxy.mjs <<'NODE'
import http from 'node:http';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const bindHost = process.env.BIND_HOST || '127.0.0.1';
const httpPort = Number(process.env.PORT || 3000);
const appPort = Number(process.env.CODEX_APP_SERVER_PORT || 8080);
const appUrl = process.env.CODEX_APP_SERVER_URL || `ws://127.0.0.1:${appPort}`;
const defaultCwd = process.env.CODEX_CWD || process.cwd();
const timeoutMs = Number(process.env.CODEX_TIMEOUT_MS || 120000);

if (bindHost !== '127.0.0.1' && bindHost !== 'localhost' && bindHost !== '::1') {
  throw new Error(`Refusing non-loopback bind host: ${bindHost}`);
}

let managedAppServer = null;
let activeRequests = 0;

function log(level, message, meta = {}) {
  const extra = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
  console.error(`[${new Date().toISOString()}] ${level.toUpperCase()} ${message}${extra}`);
}

function json(res, status, body) {
  const payload = JSON.stringify(body, null, 2);
  res.writeHead(status, {
    'content-type': 'application/json',
    'content-length': Buffer.byteLength(payload),
  });
  res.end(payload);
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.setEncoding('utf8');
    req.on('data', chunk => {
      raw += chunk;
      if (raw.length > 2_000_000) reject(new Error('Request body too large'));
    });
    req.on('end', () => {
      if (!raw.trim()) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (error) {
        reject(new Error(`Invalid JSON: ${error.message}`));
      }
    });
    req.on('error', reject);
  });
}

function contentToText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content.map(part => {
      if (typeof part === 'string') return part;
      if (part && typeof part.text === 'string') return part.text;
      if (part && typeof part.content === 'string') return part.content;
      return '';
    }).filter(Boolean).join('\n');
  }
  return '';
}

function promptFromOpenAiBody(body) {
  if (typeof body.input === 'string') return body.input;
  if (Array.isArray(body.input)) return body.input.map(contentToText).filter(Boolean).join('\n');
  if (Array.isArray(body.messages)) {
    return body.messages.map(message => {
      const role = message.role || 'user';
      return `${role}: ${contentToText(message.content)}`;
    }).join('\n');
  }
  throw new Error('Expected `input` or `messages` in request body');
}

async function waitForTcp(host, port, attempts = 40) {
  for (let i = 0; i < attempts; i += 1) {
    try {
      await new Promise((resolve, reject) => {
        const socket = new WebSocket(`ws://${host}:${port}`);
        const timer = setTimeout(() => {
          socket.close();
          reject(new Error('timeout'));
        }, 500);
        socket.addEventListener('open', () => {
          clearTimeout(timer);
          socket.close();
          resolve();
        }, { once: true });
        socket.addEventListener('error', reject, { once: true });
      });
      return true;
    } catch {
      await new Promise(resolve => setTimeout(resolve, 250));
    }
  }
  return false;
}

async function ensureAppServer() {
  const reachable = await waitForTcp('127.0.0.1', appPort, 1);
  if (reachable) {
    log('info', 'Using existing Codex app-server', { appUrl });
    return;
  }

  log('info', 'Starting managed Codex app-server', { appUrl });
  managedAppServer = spawn('codex', ['app-server', '--listen', appUrl], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: process.env,
  });
  managedAppServer.stdout.on('data', chunk => log('app-server', chunk.toString().trim()));
  managedAppServer.stderr.on('data', chunk => log('app-server', chunk.toString().trim()));
  managedAppServer.on('exit', (code, signal) => {
    log('warn', 'Codex app-server exited', { code, signal });
    managedAppServer = null;
  });

  const ready = await waitForTcp('127.0.0.1', appPort);
  if (!ready) throw new Error(`Codex app-server did not become reachable at ${appUrl}`);
}

function send(ws, payload) {
  ws.send(JSON.stringify(payload));
}

async function runCodexTurn(prompt, options = {}) {
  const cwd = options.cwd || defaultCwd;
  const output = [];

  return await new Promise((resolve, reject) => {
    const ws = new WebSocket(appUrl);
    const pending = new Map();
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error(`Codex turn timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    function cleanup() {
      clearTimeout(timer);
      for (const entry of pending.values()) clearTimeout(entry.timer);
      pending.clear();
      try { ws.close(); } catch {}
    }

    function request(method, params) {
      const id = randomUUID();
      return new Promise((resolveRequest, rejectRequest) => {
        const requestTimer = setTimeout(() => {
          pending.delete(id);
          rejectRequest(new Error(`Timed out waiting for codex app-server method ${method}`));
        }, timeoutMs);
        pending.set(id, { resolve: resolveRequest, reject: rejectRequest, timer: requestTimer });
        send(ws, { id, method, params });
      });
    }

    ws.addEventListener('open', async () => {
      try {
        await request('initialize', {
          clientInfo: {
            name: 'codex-openai-local-prompt-proxy',
            title: 'Codex OpenAI Local Prompt Proxy',
            version: '0.1.0',
          },
          capabilities: {
            experimentalApi: true,
            requestAttestation: false,
          },
        });
        send(ws, { method: 'initialized', params: {} });

        const started = await request('thread/start', { cwd, ephemeral: true });
        const threadId = started?.thread?.id;
        if (!threadId) throw new Error('codex app-server did not return thread.id');

        await request('turn/start', {
          threadId,
          input: [{ type: 'text', text: prompt, text_elements: [] }],
        });
      } catch (error) {
        cleanup();
        reject(error);
      }
    });

    ws.addEventListener('message', event => {
      let message;
      try {
        message = JSON.parse(event.data.toString());
      } catch (error) {
        log('warn', 'Ignoring non-JSON websocket message', { error: error.message });
        return;
      }

      const method = message.method || message.type;
      const params = message.params || message;

      if (message.id != null && pending.has(message.id)) {
        const entry = pending.get(message.id);
        pending.delete(message.id);
        clearTimeout(entry.timer);
        if (message.error) entry.reject(new Error(JSON.stringify(message.error)));
        else entry.resolve(message.result);
        return;
      }

      if (method === 'item/agentMessage/delta' || params.type === 'agent_message_delta') {
        const delta = params.delta || params.text || params.content || '';
        if (delta) output.push(delta);
      }

      if (method === 'item/agentMessage' || params.type === 'agent_message') {
        const text = params.text || params.content || '';
        if (text && output.length === 0) output.push(text);
      }

      if (method === 'turn/completed' || params.type === 'turn_completed') {
        cleanup();
        resolve(output.join(''));
      }

      if (method === 'turn/failed' || params.type === 'turn_failed') {
        cleanup();
        reject(new Error(params.error?.message || params.message || 'Codex turn failed'));
      }
    });

    ws.addEventListener('error', error => {
      cleanup();
      reject(new Error(`Websocket error: ${error.message || error.type || 'unknown'}`));
    });

    ws.addEventListener('close', () => {
      clearTimeout(timer);
    });
  });
}

function chatCompletionShape(body, text) {
  return {
    id: `chatcmpl_codex_${randomUUID()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: body.model || 'codex',
    choices: [{
      index: 0,
      message: { role: 'assistant', content: text },
      finish_reason: 'stop',
    }],
    usage: null,
  };
}

function responseShape(body, text) {
  return {
    id: `resp_codex_${randomUUID()}`,
    object: 'response',
    created_at: Math.floor(Date.now() / 1000),
    model: body.model || 'codex',
    status: 'completed',
    output: [{
      id: `msg_${randomUUID()}`,
      type: 'message',
      role: 'assistant',
      content: [{ type: 'output_text', text }],
    }],
    output_text: text,
    usage: null,
  };
}

await ensureAppServer();

const server = http.createServer(async (req, res) => {
  activeRequests += 1;
  const started = Date.now();
  log('info', 'request', { method: req.method, url: req.url, activeRequests });

  try {
    if (req.method === 'GET' && req.url === '/health') {
      return json(res, 200, {
        ok: true,
        base_url: `http://${bindHost}:${httpPort}`,
        codex_app_server_url: appUrl,
        active_requests: activeRequests,
      });
    }

    if (req.method !== 'POST' || !['/v1/responses', '/v1/chat/completions'].includes(req.url)) {
      return json(res, 404, { error: { message: 'Not found' } });
    }

    const body = await readJson(req);
    if (body.stream === true) {
      return json(res, 400, { error: { message: 'stream: true is not implemented by this mini proxy' } });
    }

    const prompt = promptFromOpenAiBody(body);
    const text = await runCodexTurn(prompt, body.codex || {});
    const response = req.url === '/v1/chat/completions'
      ? chatCompletionShape(body, text)
      : responseShape(body, text);
    return json(res, 200, response);
  } catch (error) {
    log('error', 'request failed', { error: error.message });
    return json(res, 500, { error: { message: error.message } });
  } finally {
    activeRequests -= 1;
    log('info', 'request complete', { method: req.method, url: req.url, ms: Date.now() - started });
  }
});

server.listen(httpPort, bindHost, () => {
  log('info', 'OpenAI-compatible local proxy listening', {
    baseUrl: `http://${bindHost}:${httpPort}`,
    appUrl,
  });
});

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

function shutdown() {
  log('info', 'Shutting down');
  server.close();
  if (managedAppServer) managedAppServer.kill('SIGTERM');
  setTimeout(() => process.exit(0), 250).unref();
}
NODE
```

3. Start it:

```sh
node /tmp/codex-openai-local-proxy.mjs
```

4. Validate it from another terminal:

```sh
curl -fsS http://127.0.0.1:3000/health
```

```sh
curl -sS http://127.0.0.1:3000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"codex","messages":[{"role":"user","content":"Reply with only: ok"}]}'
```

Acceptance criteria:
- `/health` returns JSON with `ok: true`.
- `/v1/chat/completions` returns an OpenAI-shaped response.
- The terminal logs every request and any warning/error.
- The HTTP server binds only to `127.0.0.1`.
- Ctrl-C cleans up the managed app-server process when this script started it.

Known limits:
- No SSE streaming.
- No tool/function-call mapping.
- No file upload mapping.
- Websocket protocol details may change between Codex versions; if the first
  request fails, inspect the app-server logs and adjust the websocket event
  names rather than hiding the failure.
````

## Notes

The script is intentionally disposable. If you want a maintained package with
TUI, HTTPS, token rotation, and config editing, build that as a separate app.
This prompt is for quickly asking Codex to bootstrap the bridge itself.
