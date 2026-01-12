"""
Claude MCP Server

An MCP server that allows other AI agents to interact with Claude
via the claude-agent-sdk (pure Python, no subprocess).

Enhanced with:
- A2A capability discovery via agent cards
- Hooks support for lifecycle events
- Skills support for specialized tasks
- Sub-agent spawning for dynamic delegation
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
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

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "claude-agent",
    "version": "2.0.0",
    "publisher": "Anthropic",
    "description": "Claude Code via claude-agent-sdk - Expert at reasoning, coding, and structured output",
    "strengths": [
        "deep-reasoning",
        "coding",
        "long-context",
        "structured-output",
        "file-operations",
        "multi-step-planning"
    ],
    "context_window": "200K+",
    "tools": [
        "ask_claude",
        "ask_claude_with_system",
        "ask_claude_json",
        "ask_claude_in_directory",
        "ask_claude_with_tools",
        "ask_claude_with_hooks",
        "ask_claude_with_skill",
        "spawn_claude_agent",
        "get_claude_capabilities",
        "get_claude_version"
    ],
    "supported_features": {
        "hooks": ["PreToolUse", "PostToolUse", "Notification", "Stop"],
        "skills": True,
        "sub_agents": True,
        "mcp_servers": True
    }
}


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


@mcp.tool()
async def get_claude_capabilities() -> str:
    """
    Get Claude's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Claude's capabilities,
    strengths, available tools, and supported features. Useful for
    other agents to discover what Claude can do.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_claude_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


@mcp.tool()
async def ask_claude_with_hooks(
    prompt: str,
    pre_hook: Optional[str] = None,
    post_hook: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Ask Claude with optional pre and post execution hooks.

    Hooks are shell commands that run before (pre_hook) or after (post_hook)
    Claude processes the prompt. Useful for automation workflows.

    Args:
        prompt: The question or prompt to send to Claude
        pre_hook: Optional shell command to run before Claude processes the prompt
        post_hook: Optional shell command to run after Claude completes
        working_directory: Directory context for hooks and Claude
        model: Claude model to use (default: "sonnet")

    Returns:
        Combined output: pre_hook result, Claude's response, post_hook result
    """
    logger.info(f"ask_claude_with_hooks called with model={model}")
    results = []
    cwd = working_directory or str(Path.cwd())

    # Run pre-hook if provided
    if pre_hook:
        logger.info(f"Running pre-hook: {pre_hook}")
        try:
            pre_result = subprocess.run(
                pre_hook,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            results.append(f"[PRE-HOOK OUTPUT]\n{pre_result.stdout}")
            if pre_result.stderr:
                results.append(f"[PRE-HOOK STDERR]\n{pre_result.stderr}")
        except Exception as e:
            results.append(f"[PRE-HOOK ERROR] {str(e)}")

    # Run Claude query
    claude_response = await query_claude(
        prompt=prompt,
        model=model,
        working_dir=cwd,
    )
    results.append(f"[CLAUDE RESPONSE]\n{claude_response}")

    # Run post-hook if provided
    if post_hook:
        logger.info(f"Running post-hook: {post_hook}")
        try:
            post_result = subprocess.run(
                post_hook,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            results.append(f"[POST-HOOK OUTPUT]\n{post_result.stdout}")
            if post_result.stderr:
                results.append(f"[POST-HOOK STDERR]\n{post_result.stderr}")
        except Exception as e:
            results.append(f"[POST-HOOK ERROR] {str(e)}")

    return "\n\n".join(results)


@mcp.tool()
async def ask_claude_with_skill(
    prompt: str,
    skill_name: str,
    skill_directory: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Ask Claude with a specific skill loaded for specialized tasks.

    Skills are stored as SKILL.md files that contain instructions and
    context for specialized tasks. This tool loads the skill and includes
    it in Claude's system prompt.

    Args:
        prompt: The question or prompt to send to Claude
        skill_name: Name of the skill to load (looks for {skill_name}/SKILL.md or {skill_name}.md)
        skill_directory: Optional base directory for skills (default: ./skills or ~/.claude/skills)
        working_directory: Directory context for Claude
        model: Claude model to use (default: "sonnet")

    Returns:
        Claude's response with the skill context applied
    """
    logger.info(f"ask_claude_with_skill called with skill={skill_name}, model={model}")

    # Search for skill file
    skill_content = None
    search_paths = []

    if skill_directory:
        search_paths.append(Path(skill_directory))
    search_paths.extend([
        Path.cwd() / "skills",
        Path.cwd() / ".claude" / "skills",
        Path.home() / ".claude" / "skills",
    ])

    for base_path in search_paths:
        # Try folder with SKILL.md
        skill_file = base_path / skill_name / "SKILL.md"
        if skill_file.exists():
            skill_content = skill_file.read_text()
            logger.info(f"Loaded skill from: {skill_file}")
            break
        # Try direct .md file
        skill_file = base_path / f"{skill_name}.md"
        if skill_file.exists():
            skill_content = skill_file.read_text()
            logger.info(f"Loaded skill from: {skill_file}")
            break

    if not skill_content:
        return f"Error: Skill '{skill_name}' not found in any of: {[str(p) for p in search_paths]}"

    # Build system prompt from skill
    system_prompt = f"# Skill: {skill_name}\n\n{skill_content}"

    return await query_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        working_dir=working_directory,
    )


@mcp.tool()
async def spawn_claude_agent(
    task_description: str,
    agent_instructions: str,
    working_directory: Optional[str] = None,
    allowed_tools: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_turns: int = 5,
) -> str:
    """
    Dynamically spawn a Claude sub-agent with custom instructions.

    Creates a specialized Claude instance with tailored instructions
    for a specific sub-task. Useful for breaking down complex work
    into parallel or sequential sub-agent operations.

    Args:
        task_description: Brief description of the task for the sub-agent
        agent_instructions: Detailed system instructions for the sub-agent's behavior
        working_directory: Directory context for the sub-agent
        allowed_tools: Comma-separated list of allowed tools (e.g., "Bash,Read,Edit")
        model: Claude model to use (default: "sonnet")
        max_turns: Maximum conversation turns for the sub-agent (default: 5)

    Returns:
        The sub-agent's complete response
    """
    logger.info(f"spawn_claude_agent called: task={task_description[:50]}...")

    # Build enhanced system prompt for sub-agent
    system_prompt = f"""You are a specialized sub-agent spawned for a specific task.

## Your Task
{task_description}

## Your Instructions
{agent_instructions}

## Constraints
- Focus only on the task assigned
- Be thorough but concise
- Report your findings clearly
- If you cannot complete the task, explain why
"""

    tools_list = None
    if allowed_tools:
        tools_list = [t.strip() for t in allowed_tools.replace(",", " ").split() if t.strip()]

    return await query_claude(
        prompt=f"Execute the following task:\n\n{task_description}",
        system_prompt=system_prompt,
        model=model,
        working_dir=working_directory,
        allowed_tools=tools_list,
        max_turns=max_turns,
    )


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Claude Agent MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: ask_claude, ask_claude_with_system, ask_claude_json")
    logger.info("Advanced tools: ask_claude_with_hooks, ask_claude_with_skill, spawn_claude_agent")
    logger.info("Discovery: get_claude_capabilities, get_claude_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

