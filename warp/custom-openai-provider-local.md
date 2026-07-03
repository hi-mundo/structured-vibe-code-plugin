# Warp And Local OpenAI-Compatible Providers

When using a local OpenAI-compatible endpoint from Warp, prefer a loopback URL
first:

```text
http://127.0.0.1:3000/v1
```

This avoids DNS surprises. A local hostname such as `codex.local` only works
when the client process resolves DNS on your machine and your `/etc/hosts`
contains:

```text
127.0.0.1 codex.local
```

If Warp routes the request through a remote service or cloud runtime, that
remote runtime cannot see your machine's `/etc/hosts` file. In that case,
`codex.local` may fail with a DNS error even though local `curl` works.

## Recommended Local Test

```sh
curl -fsS http://127.0.0.1:3000/health
```

```sh
curl -sS http://127.0.0.1:3000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"codex","messages":[{"role":"user","content":"Reply with only: ok"}]}'
```

If those pass but Warp still cannot connect, the issue is likely where Warp is
making the network call from. Keep the service local-only unless you explicitly
choose to expose it through a tunnel or authenticated network boundary.
