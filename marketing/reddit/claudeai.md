**Title:** Made Claude call other AI agents with MCP

Built MCP servers that let Claude invoke other AI agents as tools.

**Example:** Ask Claude to generate an image. Claude can't — but Gemini can. So Claude calls Gemini via MCP, gets the image, returns it.

Also works with:
- Aider (fast code edits)
- OpenAI Codex (sandboxed execution)
- Goose (Block's agent)

Works with Claude Desktop — just add the config.

**GitHub:** https://github.com/roeiba/agents-parliament
