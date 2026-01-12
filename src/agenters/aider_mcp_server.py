"""
Aider MCP Server

An MCP server that allows other AI agents to interact with Aider,
the AI pair programming tool.

Enhanced with:
- A2A capability discovery via agent cards
- Architect mode for planning
- Git-integrated code changes
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
logger = logging.getLogger("aider-mcp")

# Initialize FastMCP server
mcp = FastMCP("aider-agent")

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "aider-agent",
    "version": "2.0.0",
    "publisher": "Paul Gauthier (Open Source)",
    "description": "Aider - AI pair programming with Git integration and repo mapping",
    "strengths": [
        "git-integration",
        "code-editing",
        "diff-handling",
        "repo-mapping",
        "architect-mode"
    ],
    "context_window": "varies by model",
    "tools": [
        "aider_chat",
        "aider_architect",
        "aider_ask",
        "get_aider_capabilities",
        "get_aider_version"
    ],
    "supported_features": {
        "git_auto_commit": True,
        "architect_mode": True,
        "repo_map": True,
        "model_agnostic": True
    }
}


async def run_aider_command(
    args: list[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
) -> str:
    """
    Run an aider command and return the output.

    Args:
        args: Command line arguments for aider
        working_dir: Working directory for the command
        input_text: Optional input to send to stdin

    Returns:
        Command output as string
    """
    cmd = ["aider"] + args
    logger.info(f"Running aider command: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_text else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )

        stdout, stderr = await process.communicate(
            input=input_text.encode() if input_text else None
        )

        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""

        if process.returncode != 0:
            logger.warning(f"Aider returned non-zero exit code: {process.returncode}")
            if error:
                return f"Error (exit code {process.returncode}):\n{error}\n\nOutput:\n{output}"

        return output if output else error

    except FileNotFoundError:
        error_msg = "Aider CLI not found. Please install it with: pip install aider-chat"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error running aider: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def aider_chat(
    message: str,
    working_directory: str,
    files: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
) -> str:
    """
    Send a message to Aider to make changes to code.

    Args:
        message: The instruction or request for Aider
        working_directory: The directory containing the code to work on
        files: Optional comma-separated list of files to include in context
        model: The model to use (default: claude-3-5-sonnet)

    Returns:
        Aider's response and any changes made
    """
    logger.info(f"aider_chat called in {working_directory}")

    args = [
        "--model", model,
        "--yes",  # Auto-confirm changes
        "--no-git",  # Don't auto-commit (let user control git)
        "--message", message,
    ]

    if files:
        for f in files.split(","):
            args.extend(["--file", f.strip()])

    return await run_aider_command(args, working_dir=working_directory)


@mcp.tool()
async def aider_architect(
    message: str,
    working_directory: str,
    files: Optional[str] = None,
) -> str:
    """
    Use Aider in architect mode for high-level planning and design.

    Architect mode uses a two-model approach: one model for planning
    and another for implementation.

    Args:
        message: The design or planning request
        working_directory: The directory containing the code
        files: Optional comma-separated list of files to include

    Returns:
        Aider's architectural analysis and recommendations
    """
    logger.info(f"aider_architect called in {working_directory}")

    args = [
        "--architect",
        "--yes",
        "--no-git",
        "--message", message,
    ]

    if files:
        for f in files.split(","):
            args.extend(["--file", f.strip()])

    return await run_aider_command(args, working_dir=working_directory)


@mcp.tool()
async def aider_ask(
    question: str,
    working_directory: str,
    files: Optional[str] = None,
) -> str:
    """
    Ask Aider a question about the codebase without making changes.

    Args:
        question: The question to ask about the code
        working_directory: The directory containing the code
        files: Optional comma-separated list of files to analyze

    Returns:
        Aider's answer to the question
    """
    logger.info(f"aider_ask called in {working_directory}")

    args = [
        "--ask",
        "--yes",
        "--no-git",
        "--message", question,
    ]

    if files:
        for f in files.split(","):
            args.extend(["--file", f.strip()])

    return await run_aider_command(args, working_dir=working_directory)


@mcp.tool()
async def get_aider_version() -> str:
    """
    Get the version of the installed Aider CLI.

    Returns:
        Aider version information
    """
    logger.info("get_aider_version called")
    return await run_aider_command(["--version"])


@mcp.tool()
async def get_aider_capabilities() -> str:
    """
    Get Aider's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Aider's capabilities,
    strengths, available tools, and supported features.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_aider_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Aider MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: aider_chat, aider_architect, aider_ask")
    logger.info("Discovery: get_aider_capabilities, get_aider_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
