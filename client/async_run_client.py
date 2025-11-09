import argparse
import asyncio
import json
from typing import Any, Dict, Tuple

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def parse_kv_args(kvs: list[str]) -> Dict[str, Any]:
    """Parse key=value pairs with simple type coercion (bool/int/float/str)."""
    out: Dict[str, Any] = {}
    for item in kvs:
        if "=" not in item:
            raise SystemExit(f"Invalid arg '{item}'. Expected key=value format.")
        k, v = item.split("=", 1)
        k = k.strip()
        v_str = v.strip()
        v_low = v_str.lower()
        if v_low in ("true", "false"):
            out[k] = (v_low == "true")
            continue
        try:
            out[k] = int(v_str)
            continue
        except ValueError:
            pass
        try:
            out[k] = float(v_str)
            continue
        except ValueError:
            pass
        out[k] = v_str
    return out


def build_endpoint(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    p = "/" + path.strip("/") if path else ""
    return f"{base}{p}"


async def call_tool(session: ClientSession, tool: str, args: Dict[str, Any]) -> Tuple[Any, Any]:
    result = await session.call_tool(tool, arguments=args)
    # Return both unstructured and structured content when available
    unstructured = None
    if result.content:
        block = result.content[0]
        # Most servers return text for simple tools
        if hasattr(block, "text"):
            unstructured = block.text
        else:
            unstructured = str(block)
    return unstructured, getattr(result, "structuredContent", None)


async def main():
    parser = argparse.ArgumentParser(description="MCP Streamable HTTP client")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Base server URL (no trailing slash)")
    parser.add_argument("--path", default="/mcp", help="MCP endpoint path (usually /mcp)")
    parser.add_argument("--tool", default="info", help="Tool name to call (default: info)")
    parser.add_argument("--args", default="{}", help="JSON string of tool arguments (ignored if key=value pairs are provided)")
    parser.add_argument("kv", nargs="*", help="Optional key=value pairs (e.g., older_than_days=0 dry_run=true)")
    parser.add_argument("--list", action="store_true", help="List available tools and exit")
    args = parser.parse_args()

    endpoint = build_endpoint(args.server, args.path)

    # Parse arguments for tool call: prefer key=value pairs, else JSON
    if args.kv:
        tool_args = parse_kv_args(args.kv)
    else:
        try:
            raw = args.args.strip()
            # Normalize smart quotes to ASCII
            raw = (
                raw.replace("“", '"').replace("”", '"')
                   .replace("‘", "'").replace("’", "'")
            )
            # Strip matching surrounding quotes (single or double)
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
                raw = raw[1:-1]
            tool_args = json.loads(raw)
            if not isinstance(tool_args, dict):
                raise ValueError("--args must be a JSON object")
        except Exception as e:
            msg = (
                "Invalid --args JSON: "
                f"{e}\n"
                "Examples (PowerShell):\n"
                "  python client/async_run_client.py --tool preview_cleanup --args \"{""limit_per_rule"": 50}\"\n"
                "  $json = @' { ""limit_per_rule"": 50 } '@; python client/async_run_client.py --tool preview_cleanup --args $json\n"
                "Or use key=value pairs: python client/async_run_client.py --tool delete_labeled older_than_days=0 dry_run=true\n"
            )
            raise SystemExit(msg)

    async with streamablehttp_client(endpoint) as (read, write, _session_id):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            if args.list:
                tools = await session.list_tools()
                print("Available tools:")
                for t in tools.tools:
                    print(f"- {t.name}: {t.description}")
                return

            # Call the specified tool
            unstructured, structured = await call_tool(session, args.tool, tool_args)
            print("=== Tool Call Result ===")
            print(f"tool: {args.tool}")
            print("-- unstructured --")
            if isinstance(unstructured, (dict, list)):
                print(json.dumps(unstructured, indent=2))
            else:
                print(unstructured)
            print("-- structured --")
            if structured is not None:
                print(json.dumps(structured, indent=2))
            else:
                print("<none>")


if __name__ == "__main__":
    asyncio.run(main())
