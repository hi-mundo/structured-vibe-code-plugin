const baseUrl = process.env.WRAPPER_BASE_URL ?? "http://127.0.0.1:3000";

const response = await fetch(`${baseUrl}/health`);
const body = await response.text();

if (!response.ok) {
  console.error(`Health check failed: ${response.status} ${body}`);
  process.exit(1);
}

console.log(body);
