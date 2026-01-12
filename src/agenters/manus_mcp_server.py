"""
Manus CLI MCP Server

An MCP server that allows other AI agents to interact with the
Manus CLI.

Enhanced with:
- A2A capability discovery via agent cards
- Directory-scoped file operations
- Search capabilities
"""

import asyncio
import json
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (important for MCP STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("manus-mcp")

# Initialize FastMCP server
mcp = FastMCP("manus-agent")

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "manus-agent",
    "version": "2.2.0",
    "publisher": "Manus",
    "description": "Best for research, competitor analysis, multi-page data collection, and building small applications. Excels at reading and synthesizing information from multiple web sources.",
    "best_for": [
        "research",
        "competitor-analysis",
        "multi-page-data-collection",
        "web-reading",
        "small-app-building",
        "market-research",
        "information-synthesis"
    ],
    "not_for": [
        "image-generation (use gemini)",
        "complex-algorithms (use claude)",
        "git-integrated-changes (use aider)",
        "single-file-edits (use codex)",
        "ci-cd-pipelines (use goose)"
    ],
    "strengths": [
        "research",
        "data-collection",
        "web-reading",
        "small-apps",
        "synthesis"
    ],
    "context_window": "varies",
    "priority": 3,  # High priority for research and data collection tasks
    "tools": [
        "manus_prompt",
        "manus_in_directory",
        "manus_with_search",
        "get_manus_capabilities",
        "get_manus_version"
    ],
    "supported_features": {
        "search": True,
        "file_operations": True,
        "web_reading": True,
        "app_building": True
    }
}




async def run_manus_command(
    args: list[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Run a manus CLI command and return the output.

    Args:
        args: Command line arguments for manus
        working_dir: Working directory for the command
        input_text: Optional input to send to stdin
        timeout: Timeout in seconds (default 5 minutes)

    Returns:
        Command output as string
    """
    cmd = ["manus"] + args
    logger.info(f"Running manus command: {' '.join(cmd)}")

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
            logger.warning(f"Manus returned non-zero exit code: {process.returncode}")
            if error:
                return f"Error (exit code {process.returncode}):\n{error}\n\nOutput:\n{output}"

        return output if output else error

    except FileNotFoundError:
        error_msg = "Manus CLI not found. Please install it."
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error running manus: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def manus_prompt(
    prompt: str,
    working_directory: Optional[str] = None,
    model: str = "manus-1",
) -> str:
    """
    Send a prompt to the Manus CLI.

    BEST FOR: Research, competitor analysis, multi-page data collection, building small apps.
    NOT FOR: Images (use gemini), complex algorithms (use claude), git changes (use aider).

    Args:
        prompt: The question or instruction for Manus
        working_directory: Optional directory context for file operations
        model: The Manus model to use (default: manus-1)

    Returns:
        Manus's response
    """
    logger.info(f"manus_prompt called")

    args = [
        "--model", model,
        "--prompt", prompt,
    ]

    return await run_manus_command(args, working_dir=working_directory)


@mcp.tool()
async def manus_in_directory(
    prompt: str,
    working_directory: str,
    model: str = "manus-1",
) -> str:
    """
    Run Manus with access to a specific directory for file operations.

    This allows Manus to read and analyze files in the specified directory.

    Args:
        prompt: The question or instruction for Manus
        working_directory: Directory where Manus should operate
        model: The Manus model to use

    Returns:
        Manus's response
    """
    logger.info(f"manus_in_directory called in {working_directory}")

    args = [
        "--model", model,
        "--prompt", prompt,
    ]

    return await run_manus_command(args, working_dir=working_directory)


@mcp.tool()
async def manus_with_search(
    prompt: str,
    working_directory: Optional[str] = None,
) -> str:
    """
    Run Manus with search capabilities enabled.

    Args:
        prompt: The question or instruction for Manus
        working_directory: Optional directory context

    Returns:
        Manus's response
    """
    logger.info(f"manus_with_search called")

    args = [
        "--search",
        "--prompt", prompt,
    ]

    return await run_manus_command(args, working_dir=working_directory)


@mcp.tool()
async def get_manus_version() -> str:
    """
    Get the version of the installed Manus CLI.

    Returns:
        Manus CLI version information
    """
    logger.info("get_manus_version called")
    return await run_manus_command(["--version"])


@mcp.tool()
async def get_manus_capabilities() -> str:
    """
    Get Manus's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Manus's capabilities,
    strengths, available tools, and supported features. Useful for
    other agents to discover what Manus can do.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_manus_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Manus MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: manus_prompt, manus_in_directory, manus_with_search")
    logger.info("Discovery: get_manus_capabilities, get_manus_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
