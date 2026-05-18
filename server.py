"""Noisy stdio MCP server used as a log-rotation fixture for warpdotdev/warp PRs.

Warp captures every MCP server's stderr/stdout into a per-server log file
under the `mcp/` namespace. PR warpdotdev/warp#10874 adds size-based rotation
to that capture path (10 MiB per file, 5 rotated copies). To demonstrate
that rotation in a short recording you need a server that can spam more
than 10 MiB into stderr on demand — real MCP servers take hours/days to do
that, so this fixture exists.

Exposes one tool, `spam`, that writes ~N MiB of synthetic 1 KiB lines to
stderr in a single call. Default 12 MiB trips one rotation; pass a larger
value (or call the tool repeatedly) to trip more.
"""

import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("noisy-mcp")


@mcp.tool()
def spam(megabytes: int = 12) -> str:
    """Emit `megabytes` MiB of synthetic 1 KiB lines to stderr."""
    target = megabytes * 1024 * 1024
    line = ("x" * 1023) + "\n"
    written = 0
    while written < target:
        sys.stderr.write(line)
        written += len(line)
    sys.stderr.flush()
    return f"emitted {megabytes} MiB to stderr"


if __name__ == "__main__":
    mcp.run()
