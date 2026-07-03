import crypto from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import http from "node:http";
import https from "node:https";
import { resolve } from "node:path";
import readline from "node:readline/promises";
import { spawn } from "node:child_process";
import { stdin as input, stdout as output } from "node:process";
import { CodexAppServerClient } from "./codex-client.mjs";
import {
  chatCompletionResponse,
  httpError,
  messagesToCodexPrompt,
  rejectUnsupportedStream,
  responseInputToCodexPrompt,
  responsesResponse,
} from "./openai-shapes.mjs";

const args = parseArgs(process.argv.slice(2));
const tuiEnabled = !args.daemon && process.stdin.isTTY && process.stdout.isTTY;

const state = {
  bindHost: process.env.BIND_HOST ?? process.env.HOST ?? "127.0.0.1",
  publicHost: process.env.PUBLIC_HOST ?? "codex.local",
  port: Number(process.env.PORT ?? 3000),
  tlsEnabled: process.env.TLS_ENABLED !== "false",
  tlsCertDir: process.env.TLS_CERT_DIR ?? ".local/certs",
  codexManaged: !process.env.CODEX_APP_SERVER_URL,
  codexPort: Number(process.env.CODEX_APP_SERVER_PORT ?? 8080),
  codexUrl: process.env.CODEX_APP_SERVER_URL ?? `ws://127.0.0.1:${Number(process.env.CODEX_APP_SERVER_PORT ?? 8080)}`,
  codexToken: process.env.CODEX_APP_SERVER_TOKEN ?? null,
  localApiKey: process.env.LOCAL_API_KEY ?? args.apiKey ?? null,
  defaultCwd: process.env.CODEX_CWD ?? process.cwd(),
  timeoutMs: Number(process.env.CODEX_TIMEOUT_MS ?? 120_000),
};

let server = null;
let codexProcess = null;
let codexProcessStopping = false;
let codexProcessPortInUse = false;
let starting = false;
let activeRequests = 0;
let ui = null;

async function main() {
  if (tuiEnabled) {
    ui = new TerminalUi(state);
    ui.start();
    setupKeyboard();
  } else {
    log("info", "starting in daemon mode without TUI");
  }

  await ensureCodexProtocolGenerated();
  await startManagedCodexAppServer();
  await startServer();

  process.on("SIGINT", () => shutdown(0));
  process.on("SIGTERM", () => shutdown(0));
}

async function startServer() {
  if (starting) {
    return;
  }

  starting = true;

  try {
    assertLocalHost(state.bindHost);

    const nextServer = await createHttpServer();

    await new Promise((resolve, reject) => {
      nextServer.once("error", reject);
      nextServer.listen(state.port, state.bindHost, resolve);
    });

    server = nextServer;
    log("info", `listening ${serverProtocol()}://${state.bindHost}:${state.port}`);
    log("info", `public base URL ${baseUrl()}`);
    log("info", `${state.codexManaged ? "managed" : "external"} codex app-server ${state.codexUrl}`);
  } catch (error) {
    log("error", `failed to start server on ${state.bindHost}:${state.port}: ${error.message}`);
    if (!tuiEnabled) {
      process.exit(1);
    }
  } finally {
    starting = false;
    ui?.render();
  }
}

async function createHttpServer() {
  if (!state.tlsEnabled) {
    return http.createServer(handleRequest);
  }

  const tls = await ensureTlsCertificate();
  return https.createServer(tls, handleRequest);
}

async function ensureTlsCertificate() {
  const certDir = resolve(state.tlsCertDir);
  const keyPath = resolve(certDir, "codex.local.key");
  const certPath = resolve(certDir, "codex.local.crt");
  const configPath = resolve(certDir, "openssl.cnf");

  if (!existsSync(keyPath) || !existsSync(certPath)) {
    log("warn", "local TLS certificate missing; generating self-signed certificate");
    await mkdir(certDir, { recursive: true });
    await writeFile(configPath, opensslConfig(), { mode: 0o600 });
    await runCommand("openssl", [
      "req",
      "-x509",
      "-nodes",
      "-newkey",
      "rsa:2048",
      "-days",
      "825",
      "-keyout",
      keyPath,
      "-out",
      certPath,
      "-config",
      configPath,
      "-extensions",
      "v3_req",
    ], {
      label: "local TLS certificate generation",
    });
    log("info", `local TLS certificate generated at ${certPath}`);
  } else {
    log("info", "local TLS certificate found");
  }

  return {
    key: await readFile(keyPath),
    cert: await readFile(certPath),
  };
}

function opensslConfig() {
  return `[req]
default_bits = 2048
default_md = sha256
distinguished_name = dn
prompt = no

[dn]
CN = codex.local

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = codex.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
`;
}

async function stopServer() {
  if (!server) {
    return;
  }

  const current = server;
  server = null;

  await new Promise((resolve) => current.close(resolve));
  log("info", "server stopped");
}

async function restartServer() {
  log("warn", "restarting wrapper");
  await stopServer();
  await stopManagedCodexAppServer();
  await startManagedCodexAppServer();
  await startServer();
}

async function ensureCodexProtocolGenerated() {
  const outDir = resolve("generated/codex-app-server");
  const expectedFiles = [
    resolve(outDir, "ClientRequest.ts"),
    resolve(outDir, "ServerNotification.ts"),
  ];

  if (expectedFiles.every((file) => existsSync(file))) {
    log("info", "codex protocol files found");
    return;
  }

  log("warn", "codex protocol files missing; generating them now");
  await mkdir(outDir, { recursive: true });

  await runCommand("codex", ["app-server", "generate-ts", "--out", outDir, "--experimental"], {
    label: "codex protocol generation",
  });

  log("info", "codex protocol files generated");
}

async function startManagedCodexAppServer() {
  if (!state.codexManaged) {
    log("info", "using external codex app-server");
    return;
  }

  if (codexProcess) {
    return;
  }

  codexProcessStopping = false;
  codexProcessPortInUse = false;
  log("info", `starting managed codex app-server on ${state.codexUrl}`);

  codexProcess = spawn("codex", ["app-server", "--listen", state.codexUrl], {
    stdio: ["ignore", "pipe", "pipe"],
  });

  codexProcess.stdout.setEncoding("utf8");
  codexProcess.stderr.setEncoding("utf8");
  codexProcess.stdout.on("data", (chunk) => logProcessOutput("codex", chunk));
  codexProcess.stderr.on("data", (chunk) => {
    if (String(chunk).includes("Address already in use")) {
      codexProcessPortInUse = true;
    }
    logProcessOutput("codex", chunk, "warn");
  });

  codexProcess.on("error", (error) => {
    log("error", `failed to start managed codex app-server: ${error.message}`);
  });

  codexProcess.on("exit", (code, signal) => {
    const expected = codexProcessStopping;
    codexProcess = null;
    if (expected) {
      log("info", "managed codex app-server stopped");
      return;
    }

    const reason = signal ? `signal ${signal}` : `exit code ${code}`;
    if (codexProcessPortInUse) {
      log("warn", `managed codex app-server could not bind ${state.codexUrl}; continuing if an existing Codex app-server is responding`);
      return;
    }

    log("error", `managed codex app-server exited unexpectedly: ${reason}`);
  });

  await waitForCodexAppServerReady();
}

async function stopManagedCodexAppServer() {
  if (!codexProcess) {
    return;
  }

  codexProcessStopping = true;
  const child = codexProcess;
  child.kill("SIGTERM");

  await new Promise((resolveStop) => {
    const timer = setTimeout(() => {
      if (codexProcess === child) {
        child.kill("SIGKILL");
      }
      resolveStop();
    }, 2_000);

    child.once("exit", () => {
      clearTimeout(timer);
      resolveStop();
    });
  });
}

async function waitForCodexAppServerReady() {
  const started = Date.now();
  let lastError = null;

  while (Date.now() - started < 7_500) {
    try {
      const client = new CodexAppServerClient({
        url: state.codexUrl,
        token: state.codexToken,
        cwd: state.defaultCwd,
        timeoutMs: 5_000,
      });
      await client.initializeOnly();
      log("info", "managed codex app-server is ready");
      return;
    } catch (error) {
      lastError = error;
      await delay(250);
    }
  }

  log("warn", `managed codex app-server readiness check did not pass yet: ${lastError?.message ?? "unknown error"}`);
}

async function handleRequest(request, response) {
  const started = performance.now();
  activeRequests += 1;
  ui?.render();

  let status = 500;

  try {
    setCorsHeaders(response, request);

    if (request.method === "OPTIONS") {
      status = 204;
      response.writeHead(status);
      response.end();
      return;
    }

    if (request.method === "GET" && request.url === "/health") {
      status = 200;
      sendJson(response, status, {
        ok: true,
        mode: tuiEnabled ? "tui" : "daemon",
        base_url: baseUrl(),
        codex_app_server_url: state.codexUrl,
        bind_host: state.bindHost,
        public_host: state.publicHost,
        port: state.port,
        active_requests: activeRequests,
        local_auth: Boolean(state.localApiKey),
      });
      return;
    }

    if (request.method === "POST" && request.url === "/v1/responses") {
      requireLocalAuth(request);
      const body = await readJson(request);
      rejectUnsupportedStream(body);

      const prompt = responseInputToCodexPrompt(body.input);
      const codex = createCodexClient();
      const result = await codex.runPrompt({
        prompt,
        model: codexModelFromRequest(body.model),
        cwd: body.codex?.cwd ?? body.cwd ?? null,
      });

      status = 200;
      sendJson(response, status, responsesResponse({
        model: body.model,
        text: result.text,
        threadId: result.threadId,
        turnId: result.turnId,
      }));
      return;
    }

    if (request.method === "POST" && request.url === "/v1/chat/completions") {
      requireLocalAuth(request);
      const body = await readJson(request);
      rejectUnsupportedStream(body);

      const prompt = messagesToCodexPrompt(body.messages);
      const codex = createCodexClient();
      const result = await codex.runPrompt({
        prompt,
        model: codexModelFromRequest(body.model),
        cwd: body.codex?.cwd ?? body.cwd ?? null,
      });

      status = 200;
      sendJson(response, status, chatCompletionResponse({
        model: body.model,
        text: result.text,
      }));
      return;
    }

    throw httpError(404, `No route for ${request.method} ${request.url}`);
  } catch (error) {
    status = Number(error.status ?? 500);
    const message = status >= 500 ? "Internal server error" : error.message;

    if (status >= 500) {
      log("error", `${request.method} ${request.url} failed: ${error.stack ?? error.message}`);
    } else {
      log("warn", `${request.method} ${request.url} rejected: ${error.message}`);
    }

    sendJson(response, status, {
      error: {
        message,
        type: status >= 500 ? "server_error" : "invalid_request_error",
      },
    });
  } finally {
    const durationMs = Math.round(performance.now() - started);
    activeRequests -= 1;
    log(status >= 500 ? "error" : status >= 400 ? "warn" : "request", `${request.method} ${request.url} -> ${status} ${durationMs}ms`);
    ui?.render();
  }
}

function createCodexClient() {
  return new CodexAppServerClient({
    url: state.codexUrl,
    token: state.codexToken,
    cwd: state.defaultCwd,
    timeoutMs: state.timeoutMs,
  });
}

function codexModelFromRequest(model) {
  if (!model || model === "codex") {
    return null;
  }

  return model;
}

function setupKeyboard() {
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.setEncoding("utf8");

  process.stdin.on("data", async (key) => {
    if (key === "\u0003" || key === "q") {
      await shutdown(0);
      return;
    }

    if (key === "r") {
      await restartServer();
      return;
    }

    if (key === "t") {
      regenerateToken();
      return;
    }

    if (key === "c") {
      await changeConfig();
    }
  });
}

function regenerateToken() {
  state.localApiKey = crypto.randomBytes(24).toString("base64url");
  log("warn", `LOCAL_API_KEY regenerated. Use: Authorization: Bearer ${state.localApiKey}`);
  ui?.render();
}

async function changeConfig() {
  process.stdin.setRawMode(false);
  ui?.pauseForPrompt();

  const rl = readline.createInterface({ input, output });
  try {
    const bindHost = await askDefault(rl, "Bind host", state.bindHost);
    const publicHost = await askDefault(rl, "Public host", state.publicHost);
    const port = Number(await askDefault(rl, "Port", String(state.port)));
    const codexPort = Number(await askDefault(rl, "Managed Codex app-server port", String(state.codexPort)));
    const defaultCwd = await askDefault(rl, "Default cwd", state.defaultCwd);
    const timeoutMs = Number(await askDefault(rl, "Timeout ms", String(state.timeoutMs)));

    if (!Number.isInteger(port) || port <= 0 || port > 65535) {
      log("error", `invalid port: ${port}`);
      return;
    }

    if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) {
      log("error", `invalid timeout: ${timeoutMs}`);
      return;
    }

    if (!Number.isInteger(codexPort) || codexPort <= 0 || codexPort > 65535) {
      log("error", `invalid codex app-server port: ${codexPort}`);
      return;
    }

    const needsRestart = bindHost !== state.bindHost || port !== state.port || codexPort !== state.codexPort;
    state.bindHost = bindHost;
    state.publicHost = publicHost;
    state.port = port;
    state.codexPort = codexPort;
    if (state.codexManaged) {
      state.codexUrl = `ws://127.0.0.1:${codexPort}`;
    }
    state.defaultCwd = defaultCwd;
    state.timeoutMs = timeoutMs;

    log("info", "config updated");

    if (needsRestart) {
      await restartServer();
    }
  } finally {
    rl.close();
    process.stdin.setRawMode(true);
    ui?.resumeAfterPrompt();
  }
}

async function askDefault(rl, label, current) {
  const answer = await rl.question(`${label} [${current}]: `);
  return answer.trim() || current;
}

async function shutdown(code) {
  log("info", "shutting down");
  await stopServer();
  await stopManagedCodexAppServer();
  ui?.stop();
  process.exit(code);
}

function requireLocalAuth(request) {
  if (!state.localApiKey) {
    return;
  }

  const authorization = request.headers.authorization ?? "";
  if (authorization !== `Bearer ${state.localApiKey}`) {
    throw httpError(401, "Invalid LOCAL_API_KEY bearer token");
  }
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    let body = "";

    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        reject(httpError(413, "Request body too large"));
        request.destroy();
      }
    });
    request.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (error) {
        reject(httpError(400, `Invalid JSON body: ${error.message}`));
      }
    });
    request.on("error", reject);
  });
}

function sendJson(response, status, body) {
  if (response.headersSent) {
    return;
  }

  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
  });
  response.end(`${JSON.stringify(body, null, 2)}\n`);
}

function setCorsHeaders(response, request) {
  const origin = request.headers.origin;
  const allowedOrigins = new Set([
    baseUrl(),
    `${serverProtocol()}://${state.bindHost}:${state.port}`,
    `${serverProtocol()}://127.0.0.1:${state.port}`,
    `${serverProtocol()}://localhost:${state.port}`,
    `http://${state.publicHost}:${state.port}`,
    `http://${state.bindHost}:${state.port}`,
    `http://127.0.0.1:${state.port}`,
    `http://localhost:${state.port}`,
  ]);

  response.setHeader("access-control-allow-origin", allowedOrigins.has(origin) ? origin : baseUrl());
  response.setHeader("access-control-allow-methods", "GET,POST,OPTIONS");
  response.setHeader("access-control-allow-headers", "authorization,content-type");
}

function baseUrl() {
  return `${serverProtocol()}://${state.publicHost}:${state.port}`;
}

function serverProtocol() {
  return state.tlsEnabled ? "https" : "http";
}

function assertLocalHost(host) {
  if (!["127.0.0.1", "localhost", "::1"].includes(host)) {
    throw new Error(`Refusing to bind non-loopback host ${host}`);
  }
}

function log(level, message) {
  const entry = {
    level,
    message,
    time: new Date().toLocaleTimeString(),
  };

  if (ui) {
    ui.add(entry);
  } else {
    const prefix = level.toUpperCase().padEnd(7);
    console.log(`${entry.time} ${prefix} ${message}`);
  }
}

function logProcessOutput(source, chunk, level = "info") {
  for (const line of String(chunk).split(/\r?\n/)) {
    if (line.trim()) {
      log(level, `${source}: ${line.trim()}`);
    }
  }
}

function runCommand(command, args, { label }) {
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(command, args, {
      stdio: ["ignore", "pipe", "pipe"],
    });

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => logProcessOutput(label, chunk));
    child.stderr.on("data", (chunk) => logProcessOutput(label, chunk, "warn"));
    child.on("error", rejectRun);
    child.on("exit", (code) => {
      if (code === 0) {
        resolveRun();
        return;
      }

      rejectRun(new Error(`${label} failed with exit code ${code}`));
    });
  });
}

function delay(ms) {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, ms));
}

function parseArgs(argv) {
  const parsed = {
    daemon: false,
    apiKey: null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "-d" || arg === "--daemon") {
      parsed.daemon = true;
      const maybeValue = argv[index + 1];
      if (maybeValue && !maybeValue.startsWith("-")) {
        parsed.apiKey = maybeValue;
        index += 1;
      }
      continue;
    }

    if (arg === "--api-key") {
      parsed.apiKey = argv[index + 1] ?? null;
      index += 1;
    }
  }

  return parsed;
}

class TerminalUi {
  constructor(config) {
    this.config = config;
    this.logs = [];
    this.prompting = false;
  }

  start() {
    process.stdout.write("\x1b[?25l");
    this.render();
  }

  stop() {
    process.stdout.write("\x1b[?25h\x1b[0m\n");
  }

  add(entry) {
    this.logs.push(entry);
    if (this.logs.length > 200) {
      this.logs.shift();
    }
    this.render();
  }

  pauseForPrompt() {
    this.prompting = true;
    process.stdout.write("\x1b[?25h\x1b[0m\n");
  }

  resumeAfterPrompt() {
    this.prompting = false;
    process.stdout.write("\x1b[?25l");
    this.render();
  }

  render() {
    if (this.prompting) {
      return;
    }

    const rows = process.stdout.rows || 24;
    const columns = process.stdout.columns || 100;
    const logRows = Math.max(5, rows - 5);
    const visible = this.logs.slice(-logRows);

    process.stdout.write("\x1b[2J\x1b[H");
    process.stdout.write(color("Codex OpenAI Local Wrapper", "cyan"));
    process.stdout.write("\n");
    process.stdout.write(`HTTP ${baseUrl()} -> ${this.config.bindHost}:${this.config.port}  Codex ${this.config.codexUrl}  Active ${activeRequests}\n`);
    process.stdout.write(`cwd ${this.config.defaultCwd}\n`);
    process.stdout.write(`auth ${this.config.localApiKey ? mask(this.config.localApiKey) : "off"}\n`);
    process.stdout.write("".padEnd(columns, "-").slice(0, columns));
    process.stdout.write("\n");

    for (const entry of visible) {
      const line = `${entry.time} ${entry.level.toUpperCase().padEnd(7)} ${entry.message}`;
      process.stdout.write(`${colorByLevel(entry.level, line).slice(0, columns)}\n`);
    }

    const remaining = logRows - visible.length;
    for (let i = 0; i < remaining; i += 1) {
      process.stdout.write("\n");
    }

    const bar = " r restart | t regenerate token | c change config | q quit ";
    process.stdout.write(color(bar.padEnd(columns, " ").slice(0, columns), "inverse"));
  }
}

function colorByLevel(level, line) {
  if (level === "error") {
    return color(line, "red");
  }
  if (level === "warn") {
    return color(line, "yellow");
  }
  if (level === "request") {
    return color(line, "green");
  }
  return line;
}

function color(text, name) {
  const codes = {
    cyan: ["\x1b[36m", "\x1b[0m"],
    green: ["\x1b[32m", "\x1b[0m"],
    red: ["\x1b[31m", "\x1b[0m"],
    yellow: ["\x1b[33m", "\x1b[0m"],
    inverse: ["\x1b[7m", "\x1b[0m"],
  };
  const [open, close] = codes[name] ?? ["", ""];
  return `${open}${text}${close}`;
}

function mask(value) {
  if (value.length <= 8) {
    return "set";
  }

  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

await main();
