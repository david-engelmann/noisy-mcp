# noisy-mcp

Stdio MCP server that exists for one purpose: dump enough stderr to make
Warp's per-server log rotation visible in a short screen recording.
Used as the evidence fixture for [warpdotdev/warp#10874](https://github.com/warpdotdev/warp/pull/10874).

Exposes a single tool, `spam`, that emits ~N MiB of synthetic 1 KiB
lines to stderr in one call. Warp's MCP capture writes that stderr into
`mcp/<server>-<uuid>.log`; after 10 MiB the active file is renamed to
`.log.1`, `.log.2`, etc. A 12 MiB call trips exactly one rotation; two
back-to-back calls trip two.

## Setup

```sh
git clone https://github.com/david-engelmann/noisy-mcp ~/personal/noisy-mcp
cd ~/personal/noisy-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Wire into Warp

Add to `~/.warp-oss/.mcp.json` (under the `mcpServers` key — Warp expects
that wrapper):

```json
{
  "mcpServers": {
    "noisy-mcp": {
      "command": "/Users/<you>/personal/noisy-mcp/.venv/bin/python",
      "args": ["/Users/<you>/personal/noisy-mcp/server.py"],
      "env": {},
      "start_on_launch": true,
      "working_directory": null
    }
  }
}
```

Launch warp-oss; the server should connect. Ask the agent to "call the
`spam` tool from noisy-mcp twice with 12 MiB each" — the second invocation
guarantees a visible rotation in
`~/Library/Group Containers/2BBY89MBSN.dev.warp/Library/Application Support/dev.warp.WarpOss/mcp/`.

## License

MIT.
