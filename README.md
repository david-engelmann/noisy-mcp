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
that wrapper). Two ways to drive the spam:

**Auto-spam on startup (credit-free, preferred for recordings)** — set
`NOISY_MCP_AUTO_SPAM_MIB` and `NOISY_MCP_AUTO_SPAM_RATE_MIB_PER_SEC` in
the server env. The server kicks off a background thread that writes
that volume of stderr at the configured rate while the MCP handshake
stays responsive:

```json
{
  "mcpServers": {
    "noisy-mcp": {
      "command": "/Users/<you>/personal/noisy-mcp/.venv/bin/python",
      "args": ["/Users/<you>/personal/noisy-mcp/server.py"],
      "env": {
        "NOISY_MCP_AUTO_SPAM_MIB": "35",
        "NOISY_MCP_AUTO_SPAM_RATE_MIB_PER_SEC": "1.5"
      },
      "start_on_launch": true,
      "working_directory": null
    }
  }
}
```

35 MiB at 1.5 MiB/sec ≈ 24 seconds of spam, triggering ~3 rotations
visibly in `~/Library/Group Containers/2BBY89MBSN.dev.warp/Library/Application Support/dev.warp.WarpOss/mcp/`.

**Agent-driven (tool-call mode)** — omit the env vars; ask the agent to
"call the `spam` tool from noisy-mcp with megabytes=25". Each call
costs an agent credit and surfaces a tool-approval gate in the UI.

## License

MIT.
