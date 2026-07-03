import { httpError } from "./openai-shapes.mjs";

const DEFAULT_REQUEST_TIMEOUT_MS = 120_000;

export class CodexAppServerClient {
  constructor({
    url = "ws://127.0.0.1:8080",
    token = null,
    cwd = process.cwd(),
    timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS,
  } = {}) {
    this.url = url;
    this.token = token;
    this.cwd = cwd;
    this.timeoutMs = timeoutMs;
    this.nextId = 1;
  }

  async initializeOnly() {
    const ws = await this.#connect();
    const pending = new Map();

    ws.addEventListener("message", (event) => {
      let message;
      try {
        message = JSON.parse(String(event.data));
      } catch {
        return;
      }

      if (message.id != null && pending.has(message.id)) {
        const entry = pending.get(message.id);
        pending.delete(message.id);
        clearTimeout(entry.timer);

        if (message.error) {
          entry.reject(new Error(formatCodexError(message.error)));
        } else {
          entry.resolve(message.result);
        }
      }
    });

    const request = (method, params) => {
      const id = this.nextId++;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(new Error(`Timed out waiting for codex app-server method ${method}`));
        }, this.timeoutMs);

        pending.set(id, { resolve, reject, timer });
        ws.send(JSON.stringify({ id, method, params }));
      });
    };

    try {
      await request("initialize", {
        clientInfo: {
          name: "codex-openai-local-wrapper",
          title: "Codex OpenAI Local Wrapper",
          version: "0.1.0",
        },
        capabilities: {
          experimentalApi: true,
          requestAttestation: false,
        },
      });
      ws.send(JSON.stringify({ method: "initialized" }));
    } finally {
      for (const entry of pending.values()) {
        clearTimeout(entry.timer);
      }
      pending.clear();
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    }
  }

  async runPrompt({ prompt, model = null, cwd = null }) {
    if (typeof prompt !== "string" || prompt.trim().length === 0) {
      throw httpError(400, "Prompt text cannot be empty");
    }

    const ws = await this.#connect();
    const pending = new Map();
    const deltas = [];
    let threadId = null;
    let turnId = null;
    let completed = false;
    let failed = null;

    const cleanup = () => {
      for (const entry of pending.values()) {
        clearTimeout(entry.timer);
      }
      pending.clear();
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };

    ws.addEventListener("message", (event) => {
      let message;
      try {
        message = JSON.parse(String(event.data));
      } catch (error) {
        failed = new Error(`Invalid JSON from codex app-server: ${error.message}`);
        return;
      }

      if (message.id != null && pending.has(message.id)) {
        const entry = pending.get(message.id);
        pending.delete(message.id);
        clearTimeout(entry.timer);

        if (message.error) {
          entry.reject(new Error(formatCodexError(message.error)));
        } else {
          entry.resolve(message.result);
        }
        return;
      }

      if (message.method === "error") {
        failed = new Error(formatCodexError(message.params ?? message));
        return;
      }

      if (message.method === "item/agentMessage/delta" && message.params?.delta) {
        deltas.push(String(message.params.delta));
        return;
      }

      if (message.method === "turn/completed") {
        completed = true;
        turnId = message.params?.turn?.id ?? turnId;
      }
    });

    const request = (method, params) => {
      const id = this.nextId++;
      const frame = JSON.stringify({ id, method, params });

      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(new Error(`Timed out waiting for codex app-server method ${method}`));
        }, this.timeoutMs);

        pending.set(id, { resolve, reject, timer });
        ws.send(frame);
      });
    };

    try {
      await request("initialize", {
        clientInfo: {
          name: "codex-openai-local-wrapper",
          title: "Codex OpenAI Local Wrapper",
          version: "0.1.0",
        },
        capabilities: {
          experimentalApi: true,
          requestAttestation: false,
        },
      });

      ws.send(JSON.stringify({ method: "initialized" }));

      const started = await request("thread/start", {
        cwd: cwd ?? this.cwd,
        model,
        ephemeral: true,
      });

      threadId = started?.thread?.id;
      if (!threadId) {
        throw new Error("codex app-server did not return thread.id");
      }

      const turn = await request("turn/start", {
        threadId,
        input: [
          {
            type: "text",
            text: prompt,
            text_elements: [],
          },
        ],
      });
      turnId = turn?.turn?.id ?? turnId;

      await waitUntil(() => completed || failed, this.timeoutMs);

      if (failed) {
        throw failed;
      }

      return {
        text: deltas.join(""),
        threadId,
        turnId,
      };
    } finally {
      cleanup();
    }
  }

  #connect() {
    const headers = {};
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url, { headers });
      const timer = setTimeout(() => {
        reject(new Error(`Timed out connecting to codex app-server at ${this.url}`));
      }, 10_000);

      ws.addEventListener("open", () => {
        clearTimeout(timer);
        resolve(ws);
      });

      ws.addEventListener("error", () => {
        clearTimeout(timer);
        reject(new Error(`Failed to connect to codex app-server at ${this.url}`));
      });
    });
  }
}

function waitUntil(predicate, timeoutMs) {
  const started = Date.now();

  return new Promise((resolve, reject) => {
    const tick = () => {
      if (predicate()) {
        resolve();
        return;
      }

      if (Date.now() - started > timeoutMs) {
        reject(new Error("Timed out waiting for codex turn completion"));
        return;
      }

      setTimeout(tick, 50);
    };

    tick();
  });
}

function formatCodexError(error) {
  if (typeof error === "string") {
    return error;
  }

  if (error && typeof error === "object") {
    return error.message ?? JSON.stringify(error);
  }

  return "Unknown codex app-server error";
}
