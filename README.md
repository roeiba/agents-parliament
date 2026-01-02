# Cooperating Agents - MCP Servers

A collection of MCP (Model Context Protocol) servers that allow AI agents to interact with various AI coding assistants.

## Available MCP Servers

| Server | CLI Tool | Publisher |
|--------|----------|-----------|
| `claude-mcp` | Claude Code | Anthropic |
| `aider-mcp` | Aider | Open Source |
| `codex-mcp` | OpenAI Codex | OpenAI |
| `gemini-mcp` | Gemini CLI | Google |
| `goose-mcp` | Goose | Block (Square) |

## Prerequisites

- Python 3.10+
- The respective CLI tools installed (see below)

### CLI Installation

```bash
# Claude Code (required for claude-mcp)
# Install from: https://docs.anthropic.com/en/docs/claude-code

# Aider (required for aider-mcp)
pip install aider-chat

# OpenAI Codex (required for codex-mcp)
npm install -g @openai/codex

# Gemini CLI (required for gemini-mcp)
npm install -g @google/gemini-cli

# Goose (required for goose-mcp)
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash
```

## Installation

```bash
pip install "mcp[cli]"
```

## Usage

### Run servers directly

```bash
# Claude MCP Server
python src/claude_mcp_server.py

# Aider MCP Server
python src/aider_mcp_server.py

# Codex MCP Server
python src/codex_mcp_server.py

# Gemini MCP Server
python src/gemini_mcp_server.py

# Goose MCP Server
python src/goose_mcp_server.py
```

### Configure with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "claude-agent": {
      "command": "python",
      "args": ["/path/to/src/claude_mcp_server.py"]
    },
    "aider-agent": {
      "command": "python",
      "args": ["/path/to/src/aider_mcp_server.py"]
    },
    "codex-agent": {
      "command": "python",
      "args": ["/path/to/src/codex_mcp_server.py"]
    },
    "gemini-agent": {
      "command": "python",
      "args": ["/path/to/src/gemini_mcp_server.py"]
    },
    "goose-agent": {
      "command": "python",
      "args": ["/path/to/src/goose_mcp_server.py"]
    }
  }
}
```

## Available Tools

### Claude MCP Server

| Tool | Description |
|------|-------------|
| `ask_claude` | Simple prompt to Claude |
| `ask_claude_with_system` | Prompt with custom system prompt |
| `ask_claude_json` | Get structured JSON response |
| `ask_claude_in_directory` | Run with directory context |
| `ask_claude_with_tools` | Run with specific tools enabled |
| `get_claude_version` | Get CLI version |

### Aider MCP Server

| Tool | Description |
|------|-------------|
| `aider_chat` | Send a message to make code changes |
| `aider_architect` | Use architect mode for planning |
| `aider_ask` | Ask questions without making changes |
| `get_aider_version` | Get Aider version |

### Codex MCP Server

| Tool | Description |
|------|-------------|
| `codex_prompt` | Send a prompt (suggest mode) |
| `codex_full_auto` | Run in full-auto sandboxed mode |
| `codex_auto_edit` | Run in auto-edit mode |
| `get_codex_version` | Get Codex CLI version |

### Gemini MCP Server

| Tool | Description |
|------|-------------|
| `gemini_prompt` | Send a prompt to Gemini |
| `gemini_in_directory` | Run with directory context |
| `gemini_with_search` | Run with Google Search grounding |
| `get_gemini_version` | Get Gemini CLI version |

### Goose MCP Server

| Tool | Description |
|------|-------------|
| `goose_run` | Run with text instructions |
| `goose_run_file` | Run with instructions from file |
| `goose_run_recipe` | Run a predefined recipe |
| `get_goose_version` | Get Goose version |

## License

MIT
