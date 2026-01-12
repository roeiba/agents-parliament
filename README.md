# Agents Parliament

![Agents Parliament](agents_parliament.png)

[![PyPI version](https://img.shields.io/pypi/v/agenters.svg)](https://pypi.org/project/agenters/)

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

## Provisioning

The `agenters` CLI provides easy provisioning for your environment.

### Check Status

See what's currently configured:

```bash
agenters status
```

### Quick Provisioning

```bash
# Provision all agents globally for Cursor
agenters provision --global --client cursor --agents all --yes

# Provision specific agents for a project
agenters provision --project --agents claude,aider

# Preview changes without applying (dry-run)
agenters provision --global --client vscode --dry-run
```

### Supported Clients

| Client Flag | Description |
|-------------|-------------|
| `--client claude` | Claude Desktop |
| `--client cursor` | Cursor IDE |
| `--client vscode` | VS Code |
| `--client windsurf` | Windsurf |
| `--client antigravity` | Antigravity (Gemini) |

### Interactive Install/Uninstall

For an interactive experience:

```bash
# Interactive installer with step-by-step prompts
agenters install

# Interactive uninstaller
agenters uninstall
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

### Claude MCP Server (v2.0 - A2A Enhanced)

| Tool | Description |
|------|-------------|
| `ask_claude` | Simple prompt to Claude |
| `ask_claude_with_system` | Prompt with custom system prompt |
| `ask_claude_json` | Get structured JSON response |
| `ask_claude_in_directory` | Run with directory context |
| `ask_claude_with_tools` | Run with specific tools enabled |
| `ask_claude_with_hooks` | Execute with pre/post hooks |
| `ask_claude_with_skill` | Load a skill for specialized tasks |
| `spawn_claude_agent` | Create a sub-agent with custom instructions |
| `get_claude_capabilities` | Get agent card for A2A discovery |
| `get_claude_version` | Get CLI version |

### Aider MCP Server (v2.0 - A2A Enhanced)

| Tool | Description |
|------|-------------|
| `aider_chat` | Send a message to make code changes |
| `aider_architect` | Use architect mode for planning |
| `aider_ask` | Ask questions without making changes |
| `get_aider_capabilities` | Get agent card for A2A discovery |
| `get_aider_version` | Get Aider version |

### Codex MCP Server (v2.0 - A2A Enhanced)

| Tool | Description |
|------|-------------|
| `codex_prompt` | Send a prompt (suggest mode) |
| `codex_full_auto` | Run in full-auto sandboxed mode |
| `codex_auto_edit` | Run in auto-edit mode |
| `get_codex_capabilities` | Get agent card for A2A discovery |
| `get_codex_version` | Get Codex CLI version |

### Gemini MCP Server (v2.0 - A2A Enhanced)

| Tool | Description |
|------|-------------|
| `gemini_prompt` | Send a prompt to Gemini |
| `gemini_in_directory` | Run with directory context |
| `gemini_with_search` | Run with Google Search grounding |
| `gemini_with_playbook` | Execute with a specialized playbook |
| `get_gemini_capabilities` | Get agent card for A2A discovery |
| `get_gemini_version` | Get Gemini CLI version |

### Goose MCP Server (v2.0 - A2A Enhanced)

| Tool | Description |
|------|-------------|
| `goose_run` | Run with text instructions |
| `goose_run_file` | Run with instructions from file |
| `goose_run_recipe` | Run a predefined recipe |
| `goose_with_toolkits` | Run with specific toolkits enabled |
| `get_goose_capabilities` | Get agent card for A2A discovery |
| `get_goose_version` | Get Goose version |

## A2A Protocol & Mesh Coordination

The Agents Parliament now supports **agent-to-agent (A2A) communication** and **full mesh coordination**.

### Agent Capability Discovery

Each agent exposes a `get_*_capabilities` tool that returns an agent card:

```python
from agenters.a2a_protocol import discover_agents, find_best_agent

# Discover all agents
agents = discover_agents()
for agent in agents:
    print(f"{agent.name}: {agent.strengths}")

# Find best agent for a task
agent = find_best_agent("search the web for latest Python trends")
# Returns: gemini-agent (has search-grounding strength)
```

### Mesh Coordination

Route tasks to the best agent based on capabilities:

```python
from agenters.mesh_coordinator import create_mesh

mesh = create_mesh()

# Find best agent for a task
agent, reasoning = mesh.route_to_best_agent("Refactor this code with Git commits")
# agent: aider-agent, reasoning: git-integration strength

# Suggest a team for complex tasks
team = mesh.suggest_team("Research latest APIs, implement feature, and deploy")
# Returns: [(gemini-agent, "Research"), (claude-agent, "Implement"), (goose-agent, "Deploy")]
```

### Advanced Features

| Feature | Agent | Description |
|---------|-------|-------------|
| **Hooks** | Claude | Execute shell commands before/after prompts |
| **Skills** | Claude | Load specialized SKILL.md files |
| **Sub-agents** | Claude | Spawn task-specific agents dynamically |
| **Playbooks** | Gemini | Pre-configured workflow guides |
| **Toolkits** | Goose | Enable MCP extensions (GitHub, Jira, etc.) |
| **Recipes** | Goose | YAML-defined reusable workflows |
| **Architect Mode** | Aider | Two-model planning approach |
| **Full-Auto** | Codex | Sandboxed autonomous execution |

For detailed documentation, see [docs/advanced_features.md](docs/advanced_features.md).

## License

MIT

