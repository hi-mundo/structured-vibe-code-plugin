import { mkdir } from "node:fs/promises";
import { spawn } from "node:child_process";
import { resolve } from "node:path";

const outDir = resolve("generated/codex-app-server");

await mkdir(outDir, { recursive: true });

const child = spawn(
  "codex",
  ["app-server", "generate-ts", "--out", outDir, "--experimental"],
  { stdio: "inherit" },
);

const exitCode = await new Promise((resolveExit) => {
  child.on("close", resolveExit);
  child.on("error", (error) => {
    console.error("Failed to run codex app-server generate-ts:", error.message);
    resolveExit(1);
  });
});

if (exitCode !== 0) {
  console.error(`codex protocol generation failed with exit code ${exitCode}`);
  process.exit(exitCode ?? 1);
}

console.log(`Generated Codex app-server protocol files in ${outDir}`);
