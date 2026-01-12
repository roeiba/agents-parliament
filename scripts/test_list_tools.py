#!/usr/bin/env python3
"""Test script to verify list_tools works on all MCP servers using MCP SDK."""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVERS = ["claude-mcp", "gemini-mcp", "codex-mcp", "aider-mcp", "goose-mcp", "manus-mcp"]


async def test_server(cmd: str) -> None:
    """Test a single MCP server's list_tools response."""
    print(f"\n{'='*50}")
    print(f"Testing: {cmd}")
    print('='*50)
    
    try:
        server_params = StdioServerParameters(command=cmd, args=[])
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                
                print(f"✓ Found {len(result.tools)} tools:")
                for tool in result.tools:
                    desc = tool.description.strip().replace('\n', ' ')[:50] if tool.description else 'No description'
                    print(f"  - {tool.name}: {desc}...")
                    
    except FileNotFoundError:
        print(f"✗ {cmd} not installed")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


async def main():
    for server in SERVERS:
        try:
            await asyncio.wait_for(test_server(server), timeout=15)
        except asyncio.TimeoutError:
            print(f"\n{'='*50}")
            print(f"Testing: {server}")
            print('='*50)
            print(f"✗ Timed out after 15 seconds")


if __name__ == "__main__":
    asyncio.run(main())
