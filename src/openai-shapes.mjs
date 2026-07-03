export function messagesToCodexPrompt(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    throw httpError(400, "`messages` must be a non-empty array");
  }

  return messages
    .map((message) => {
      if (!message || typeof message !== "object") {
        throw httpError(400, "Each message must be an object");
      }

      const role = typeof message.role === "string" ? message.role : "user";
      const content = normalizeContent(message.content);
      return `${role}: ${content}`;
    })
    .join("\n\n");
}

export function responseInputToCodexPrompt(input) {
  if (typeof input === "string") {
    return input;
  }

  if (Array.isArray(input)) {
    return input
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (!item || typeof item !== "object") {
          throw httpError(400, "`input` items must be strings or objects");
        }

        if (typeof item.content === "string") {
          return item.content;
        }

        if (Array.isArray(item.content)) {
          return item.content.map(normalizeContentPart).join("");
        }

        if (typeof item.text === "string") {
          return item.text;
        }

        return JSON.stringify(item);
      })
      .join("\n\n");
  }

  throw httpError(400, "`input` must be a string or an array");
}

export function chatCompletionResponse({ model, text }) {
  const created = Math.floor(Date.now() / 1000);
  const id = `chatcmpl_codex_${crypto.randomUUID()}`;

  return {
    id,
    object: "chat.completion",
    created,
    model: model ?? "codex-app-server",
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content: text,
        },
        finish_reason: "stop",
      },
    ],
    usage: null,
  };
}

export function responsesResponse({ model, text, threadId, turnId }) {
  const id = `resp_codex_${crypto.randomUUID()}`;

  return {
    id,
    object: "response",
    created_at: Math.floor(Date.now() / 1000),
    model: model ?? "codex-app-server",
    status: "completed",
    output_text: text,
    codex: {
      thread_id: threadId,
      turn_id: turnId,
    },
    output: [
      {
        id: `msg_${crypto.randomUUID()}`,
        type: "message",
        role: "assistant",
        content: [
          {
            type: "output_text",
            text,
          },
        ],
      },
    ],
    usage: null,
  };
}

export function rejectUnsupportedStream(body) {
  if (body?.stream === true) {
    throw httpError(501, "`stream: true` is not implemented in this local wrapper yet");
  }
}

export function httpError(status, message) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function normalizeContent(content) {
  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {
    return content.map(normalizeContentPart).join("");
  }

  if (content == null) {
    return "";
  }

  return JSON.stringify(content);
}

function normalizeContentPart(part) {
  if (typeof part === "string") {
    return part;
  }

  if (!part || typeof part !== "object") {
    return "";
  }

  if (typeof part.text === "string") {
    return part.text;
  }

  if (typeof part.input_text === "string") {
    return part.input_text;
  }

  return "";
}
