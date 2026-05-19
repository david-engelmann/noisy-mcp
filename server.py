"""Noisy stdio MCP server used as a log-rotation fixture for warpdotdev/warp PRs.

Warp captures every MCP server's stderr/stdout into a per-server log file
under the `mcp/` namespace. PR warpdotdev/warp#10874 adds size-based rotation
to that capture path (10 MiB per file, 5 rotated copies). To demonstrate
that rotation in a short recording you need a server that can spam more
than 10 MiB into stderr — real MCP servers take hours/days to do that,
so this fixture exists.

Two modes:

- **Tool-driven**: the agent calls the `spam(megabytes)` tool. Each call
  costs an agent credit and triggers a tool-approval gate in the UI.
- **Auto-spam on startup** (preferred for credit-free recordings): set
  `NOISY_MCP_AUTO_SPAM_MIB=<int>` in the server's environment (via the
  `env` field of `~/.warp-oss/.mcp.json`). The server kicks off a
  background thread on import that emits that many MiB of synthetic
  1 KiB lines to stderr at the rate configured by
  `NOISY_MCP_AUTO_SPAM_RATE_MIB_PER_SEC` (default 1.0). The MCP
  initialize/tools handshake remains responsive throughout.
"""

import os
import sys
import threading
import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("noisy-mcp")


def _emit_bytes(total_mib: int, rate_mib_per_sec: float) -> None:
    """Write `total_mib` MiB of synthetic 1 KiB stderr lines, rate-limited.

    Per-line pacing: write one 1 KiB line, flush, sleep. This matters
    because Warp's MCP stderr forwarder reads with `read_line` — if many
    lines arrive in the pipe before a single `read_line` call returns,
    they all coalesce into one `logger.log(...)` invocation, which then
    appears as one large entry in the simple_logger rotation loop and
    inflates per-file sizes far past the configured 10 MiB threshold.
    By flushing and sleeping per line we keep the pipe one-line-deep so
    the receiver's read_line returns one line at a time.
    """
    target = total_mib * 1024 * 1024
    line = ("x" * 1023) + "\n"  # 1024 bytes per line
    line_len = len(line)
    bytes_per_sec = max(1.0, rate_mib_per_sec * 1024 * 1024)
    sleep_per_line = line_len / bytes_per_sec
    written = 0
    while written < target:
        sys.stderr.write(line)
        sys.stderr.flush()
        written += line_len
        time.sleep(sleep_per_line)
    sys.stderr.flush()


@mcp.tool()
def spam(megabytes: int = 12) -> str:
    """Emit `megabytes` MiB of synthetic 1 KiB lines to stderr."""
    _emit_bytes(megabytes, rate_mib_per_sec=float("inf"))
    return f"emitted {megabytes} MiB to stderr"


def _maybe_autospam() -> None:
    """Honor env-var-configured background spam on startup."""
    raw = os.environ.get("NOISY_MCP_AUTO_SPAM_MIB")
    if not raw:
        return
    try:
        total = int(raw)
    except ValueError:
        return
    if total <= 0:
        return
    rate_raw = os.environ.get("NOISY_MCP_AUTO_SPAM_RATE_MIB_PER_SEC", "1.0")
    try:
        rate = float(rate_raw)
    except ValueError:
        rate = 1.0
    threading.Thread(
        target=_emit_bytes,
        args=(total, rate),
        daemon=True,
        name="noisy-mcp-autospam",
    ).start()


if __name__ == "__main__":
    _maybe_autospam()
    mcp.run()
