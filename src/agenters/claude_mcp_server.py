"""
Claude MCP Server

An MCP server that allows other AI agents to interact with Claude
via the claude-agent-sdk (pure Python, no subprocess).
"""

import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Import claude-agent-sdk components
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Configure logging to stderr (important for MCP STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("claude-agent-mcp")

# Initialize FastMCP server
mcp = FastMCP("claude-agent")

# Default settings
DEFAULT_MODEL = "sonnet"


async def query_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_turns: int = 10,
    working_dir: Optional[str] = None,
    allowed_tools: Optional[list[str]] = None,
) -> str:
    """
    Query Claude using the claude-agent-sdk.

    Args:
        prompt: The prompt to send to Claude
        system_prompt: Optional system prompt
        model: Model to use (e.g., "sonnet", "opus")
        max_turns: Maximum conversation turns
        working_dir: Working directory for file operations
        allowed_tools: List of allowed tools

    Returns:
        Claude's response text
    """
    # Build options
    options = ClaudeAgentOptions(
        model=model,
        max_turns=max_turns,
    )
    
    if system_prompt:
        options.system_prompt = system_prompt
    
    if working_dir:
        options.cwd = working_dir
    
    if allowed_tools:
        options.allowed_tools = allowed_tools
        options.permission_mode = "acceptEdits"

    prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
    logger.info(f"Querying Claude: model={model}, prompt={prompt_preview!r}")

    try:
        # Collect response from async iterator
        response_parts = []
        message_count = 0
        
        async for message in query(prompt=prompt, options=options):
            message_count += 1
            logger.debug(f"Received message {message_count}: {type(message).__name__}")
            
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
                        logger.debug(f"Text block: {block.text[:100]}...")

        result = "\n".join(response_parts)
        logger.info(f"Query complete. Messages: {message_count}, Response length: {len(result)}")
        return result if result else "No response received from Claude."

    except Exception as e:
        error_msg = f"Error querying Claude: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def ask_claude(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Ask Claude a question and get a response.

    Args:
        prompt: The question or prompt to send to Claude
        model: Claude model to use (default: "sonnet", options: "sonnet", "opus", or full model name)

    Returns:
        Claude's response text
    """
    logger.info(f"ask_claude called with model={model}")
    return await query_claude(prompt=prompt, model=model)


@mcp.tool()
async def ask_claude_with_system(
    prompt: str,
    system_prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Ask Claude a question with a custom system prompt.

    Args:
        prompt: The question or prompt to send to Claude
        system_prompt: Custom system prompt to set Claude's behavior/persona
        model: Claude model to use (default: "sonnet")

    Returns:
        Claude's response text
    """
    logger.info(f"ask_claude_with_system called with model={model}")
    return await query_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
    )


@mcp.tool()
async def ask_claude_json(
    prompt: str,
    json_schema: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Ask Claude a question and get a structured JSON response.

    Args:
        prompt: The question or prompt to send to Claude
        json_schema: JSON Schema for structured output validation.
                    Example: '{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}'
        model: Claude model to use (default: "sonnet")
        system_prompt: Optional custom system prompt

    Returns:
        Claude's response as JSON
    """
    logger.info(f"ask_claude_json called with model={model}")
    
    # Add JSON instruction to prompt
    json_prompt = f"{prompt}\n\nRespond with valid JSON matching this schema: {json_schema}"
    
    return await query_claude(
        prompt=json_prompt,
        system_prompt=system_prompt,
        model=model,
    )


@mcp.tool()
async def ask_claude_in_directory(
    prompt: str,
    working_directory: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Ask Claude a question with access to a specific directory context.

    This allows Claude to read/analyze files in the specified directory.

    Args:
        prompt: The question or prompt to send to Claude
        working_directory: Directory path where Claude should operate
        model: Claude model to use (default: "sonnet")
        system_prompt: Optional custom system prompt

    Returns:
        Claude's response text
    """
    logger.info(f"ask_claude_in_directory called with model={model}, dir={working_directory}")
    return await query_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        working_dir=working_directory,
    )


@mcp.tool()
async def ask_claude_with_tools(
    prompt: str,
    allowed_tools: str,
    working_directory: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Ask Claude a question with specific tools enabled.

    Args:
        prompt: The question or prompt to send to Claude
        allowed_tools: Comma or space-separated list of allowed tools (e.g., "Bash,Edit,Read" or "Bash(git:*)")
        working_directory: Optional directory path where Claude should operate
        model: Claude model to use (default: "sonnet")
        system_prompt: Optional custom system prompt

    Returns:
        Claude's response text
    """
    logger.info(f"ask_claude_with_tools called with model={model}, tools={allowed_tools}")
    
    # Parse tools list
    tools_list = [t.strip() for t in allowed_tools.replace(",", " ").split() if t.strip()]
    
    return await query_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        working_dir=working_directory,
        allowed_tools=tools_list,
    )


@mcp.tool()
async def get_claude_version() -> str:
    """
    Get the version of the installed Claude CLI.

    Returns:
        Claude CLI version information
    """
    logger.info("get_claude_version called")
    try:
        import claude_agent_sdk
        version = getattr(claude_agent_sdk, "__version__", "unknown")
        return f"claude-agent-sdk version: {version}"
    except Exception as e:
        return f"Error getting version: {str(e)}"


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Claude Agent MCP Server (using claude-agent-sdk)")
    logger.info("=" * 60)
    logger.info("Tools: ask_claude, ask_claude_with_system, ask_claude_json, ask_claude_in_directory, ask_claude_with_tools, get_claude_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
