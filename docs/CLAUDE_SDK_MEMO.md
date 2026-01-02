# Claude Agent SDK - Research Memo

## Package Info
- **Name:** `claude-agent-sdk` (successor to deprecated `claude-code-sdk`)
- **Install:** `pip install claude-agent-sdk`
- **Python:** 3.10+
- **Docs:** https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python

## Key Concepts

### 1. `query()` - Simple Async Iterator
```python
from claude_agent_sdk import query, AssistantMessage, TextBlock
import anyio

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

anyio.run(main)
```

### 2. `ClaudeAgentOptions` - Configuration
```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant",
    max_turns=1,
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits',  # auto-accept file edits
    cwd="/path/to/project"          # working directory
)
```

### 3. `ClaudeSDKClient` - Interactive Sessions
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(...)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Hello Claude")
    async for msg in client.receive_response():
        print(msg)
```

### 4. Custom Tools (In-Process MCP Servers)
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {
        "content": [
            {"type": "text", "text": f"Hello, {args['name']}!"}
        ]
    }

server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user]
)

options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__greet"]
)
```

## Benefits Over CLI
- **No subprocess management** - runs in-process
- **Better performance** - no IPC overhead
- **Type safety** - native Python types
- **Easier debugging** - single process

## For Our MCP Server
We'll use `query()` for simple one-shot calls since it's perfect for MCP tools.
The response is an async iterator yielding messages until completion.
