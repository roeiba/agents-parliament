"""
Google Gemini CLI MCP Server

An MCP server that allows other AI agents to interact with the
Google Gemini CLI.

Enhanced with:
- A2A capability discovery via agent cards
- Extensions support with playbooks
- Google Search grounding
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (important for MCP STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("gemini-mcp")

# Initialize FastMCP server
mcp = FastMCP("gemini-agent")

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "gemini-agent",
    "version": "2.1.0",
    "publisher": "Google",
    "description": "Best for image generation, web browsing/research, and web development. Has the largest context window (1M+) for massive codebase analysis.",
    "best_for": [
        "image-generation",
        "web-browsing",
        "web-research",
        "real-time-information",
        "web-development",
        "frontend-development",
        "large-codebase-analysis",
        "multimodal-tasks"
    ],
    "not_for": [
        "complex-algorithms (use claude)",
        "git-integrated-changes (use aider)",
        "small-focused-edits (use codex)",
        "autonomous-workflows (use goose)"
    ],
    "strengths": [
        "image-generation",
        "search-grounding",
        "massive-context-1M+",
        "web-development",
        "multimodal"
    ],
    "context_window": "1M+",
    "priority": 2,  # High priority for visual and web tasks
    "tools": [
        "gemini_prompt",
        "gemini_in_directory",
        "gemini_with_search",
        "gemini_with_playbook",
        "get_gemini_capabilities",
        "get_gemini_version"
    ],
    "supported_features": {
        "extensions": True,
        "playbooks": True,
        "search_grounding": True,
        "image_generation": True,
        "mcp_client": True
    }
}



async def run_gemini_command(
    args: list[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Run a gemini CLI command and return the output.

    Args:
        args: Command line arguments for gemini
        working_dir: Working directory for the command
        input_text: Optional input to send to stdin
        timeout: Timeout in seconds (default 5 minutes)

    Returns:
        Command output as string
    """
    cmd = ["gemini"] + args
    logger.info(f"Running gemini command: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_text else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_text.encode() if input_text else None),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            return f"Error: Command timed out after {timeout} seconds"

        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""

        if process.returncode != 0:
            logger.warning(f"Gemini returned non-zero exit code: {process.returncode}")
            if error:
                return f"Error (exit code {process.returncode}):\n{error}\n\nOutput:\n{output}"

        return output if output else error

    except FileNotFoundError:
        error_msg = "Gemini CLI not found. Please install it with: npm install -g @anthropic-ai/gemini-cli"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error running gemini: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def gemini_prompt(
    prompt: str,
    working_directory: Optional[str] = None,
    model: str = "gemini-2.5-pro",
) -> str:
    """
    Send a prompt to the Google Gemini CLI.

    BEST FOR: Image generation, web browsing/research, web development, large codebase analysis (1M+ context).
    NOT FOR: Complex algorithms (use claude), git changes (use aider), small edits (use codex).

    Args:
        prompt: The question or instruction for Gemini
        working_directory: Optional directory context for file operations
        model: The Gemini model to use (default: gemini-2.5-pro)

    Returns:
        Gemini's response
    """
    logger.info(f"gemini_prompt called")

    args = [
        "--model", model,
        "--prompt", prompt,
    ]

    return await run_gemini_command(args, working_dir=working_directory)


@mcp.tool()
async def gemini_in_directory(
    prompt: str,
    working_directory: str,
    model: str = "gemini-2.5-pro",
) -> str:
    """
    Run Gemini with access to a specific directory for file operations.

    This allows Gemini to read and analyze files in the specified directory.

    Args:
        prompt: The question or instruction for Gemini
        working_directory: Directory where Gemini should operate
        model: The Gemini model to use

    Returns:
        Gemini's response
    """
    logger.info(f"gemini_in_directory called in {working_directory}")

    args = [
        "--model", model,
        "--prompt", prompt,
    ]

    return await run_gemini_command(args, working_dir=working_directory)


@mcp.tool()
async def gemini_with_search(
    prompt: str,
    working_directory: Optional[str] = None,
) -> str:
    """
    Run Gemini with Google Search grounding enabled.

    This allows Gemini to search the web for up-to-date information
    when answering the prompt.

    Args:
        prompt: The question or instruction for Gemini
        working_directory: Optional directory context

    Returns:
        Gemini's response with search-grounded information
    """
    logger.info(f"gemini_with_search called")

    args = [
        "--search",
        "--prompt", prompt,
    ]

    return await run_gemini_command(args, working_dir=working_directory)


@mcp.tool()
async def get_gemini_version() -> str:
    """
    Get the version of the installed Gemini CLI.

    Returns:
        Gemini CLI version information
    """
    logger.info("get_gemini_version called")
    return await run_gemini_command(["--version"])


@mcp.tool()
async def get_gemini_capabilities() -> str:
    """
    Get Gemini's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Gemini's capabilities,
    strengths, available tools, and supported features. Useful for
    other agents to discover what Gemini can do.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_gemini_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


@mcp.tool()
async def gemini_with_playbook(
    prompt: str,
    playbook_name: str,
    playbook_directory: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: str = "gemini-2.5-pro",
) -> str:
    """
    Run Gemini with a specific playbook for specialized workflows.

    Playbooks are markdown files that teach Gemini how to effectively
    use integrated tools for specific tasks. They contain instructions,
    examples, and best practices.

    Args:
        prompt: The question or instruction for Gemini
        playbook_name: Name of the playbook (looks for {name}.md or {name}/playbook.md)
        playbook_directory: Optional base directory for playbooks (default: ./playbooks)
        working_directory: Directory context for Gemini
        model: The Gemini model to use (default: gemini-2.5-pro)

    Returns:
        Gemini's response with playbook context applied
    """
    logger.info(f"gemini_with_playbook called with playbook={playbook_name}")

    # Search for playbook file
    playbook_content = None
    search_paths = []

    if playbook_directory:
        search_paths.append(Path(playbook_directory))
    search_paths.extend([
        Path.cwd() / "playbooks",
        Path.cwd() / ".gemini" / "playbooks",
        Path.home() / ".gemini" / "playbooks",
    ])

    for base_path in search_paths:
        # Try folder with playbook.md
        playbook_file = base_path / playbook_name / "playbook.md"
        if playbook_file.exists():
            playbook_content = playbook_file.read_text()
            logger.info(f"Loaded playbook from: {playbook_file}")
            break
        # Try direct .md file
        playbook_file = base_path / f"{playbook_name}.md"
        if playbook_file.exists():
            playbook_content = playbook_file.read_text()
            logger.info(f"Loaded playbook from: {playbook_file}")
            break

    if not playbook_content:
        return f"Error: Playbook '{playbook_name}' not found in: {[str(p) for p in search_paths]}"

    # Combine playbook with prompt
    enhanced_prompt = f"""# Playbook: {playbook_name}

{playbook_content}

---

# User Request

{prompt}"""

    args = [
        "--model", model,
        "--prompt", enhanced_prompt,
    ]

    return await run_gemini_command(args, working_dir=working_directory)


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Google Gemini MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: gemini_prompt, gemini_in_directory, gemini_with_search")
    logger.info("Advanced tools: gemini_with_playbook")
    logger.info("Discovery: get_gemini_capabilities, get_gemini_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

