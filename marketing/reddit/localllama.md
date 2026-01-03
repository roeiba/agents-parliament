**Title:** MCP servers that let AI coding agents call each other

Built a set of MCP servers that enable agent-to-agent communication.

**The setup:** Your main agent (e.g., Claude) can invoke other agents as tools — Gemini for image generation, Aider for fast edits, Codex for sandboxed execution.

**Currently supports:** Claude Code, Gemini CLI, OpenAI Codex, Aider, Goose

Pure Python, uses the MCP SDK. Easy to extend if you want to add local models.

**GitHub:** https://github.com/roeiba/agents-parliament

Would love feedback on adding local LLM support.
