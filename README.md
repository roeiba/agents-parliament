# Agents Parliament

![Agents Parliament](agents_parliament.png)


The idea: instead of asking one AI coding agent (Claude, Gemini, Codex, Aider, etc.), you group them into your **"Agents Parliament."**

When you submit a task:

1. **Your main agent receives the request** and decides if it needs help
2. **It calls other agents as tools** — Claude might ask Gemini for a code review, or delegate a refactor to Aider
3. **The agents collaborate** — each bringing their strengths to produce better results

Each agent can also spawn sub-agents on the fly, dynamically creating their instructions based on the task.

## Supported Agents

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
# Install from PyPI (recommended)
pip install agenters

# OR install from source
git clone https://github.com/roeiba/agenters.git
cd agenters
pip install .
```

## Usage

### Run servers directly

Once installed, you can use the CLI commands directly:

```bash
# Claude MCP Server
claude-mcp

# Aider MCP Server
aider-mcp

# Codex MCP Server
codex-mcp

# Gemini MCP Server
gemini-mcp

# Goose MCP Server
goose-mcp
```

### Configure with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "claude-agent": {
      "command": "claude-mcp",
      "args": []
    },
    "aider-agent": {
      "command": "aider-mcp",
      "args": []
    },
    "codex-agent": {
      "command": "codex-mcp",
      "args": []
    },
    "gemini-agent": {
      "command": "gemini-mcp",
      "args": []
    },
    "goose-agent": {
      "command": "goose-mcp",
      "args": []
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
