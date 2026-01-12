"""
OpenAI Codex MCP Server

An MCP server that allows other AI agents to interact with the
OpenAI Codex CLI.

Enhanced with:
- A2A capability discovery via agent cards
- Multiple approval modes (suggest, auto-edit, full-auto)
- Sandboxed execution support
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
logger = logging.getLogger("codex-mcp")

# Initialize FastMCP server
mcp = FastMCP("codex-agent")

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "codex-agent",
    "version": "2.1.0",
    "publisher": "OpenAI",
    "description": "Best for small, focused code edits and quick one-shot tasks. Optimized for pinpointed changes rather than large refactors.",
    "best_for": [
        "small-code-edits",
        "quick-bug-fixes",
        "one-shot-tasks",
        "natural-language-to-code",
        "sandboxed-execution",
        "simple-refactors",
        "adding-single-function"
    ],
    "not_for": [
        "complex-algorithms (use claude)",
        "large-refactoring (use aider)",
        "image-generation (use gemini)",
        "web-browsing (use gemini)",
        "multi-step-workflows (use goose)"
    ],
    "strengths": [
        "quick-focused-edits",
        "sandboxed-execution",
        "natural-language-parsing",
        "fast-turnaround"
    ],
    "context_window": "varies by model",
    "priority": 4,  # Use for simple tasks, defer complex to others
    "tools": [
        "codex_prompt",
        "codex_full_auto",
        "codex_auto_edit",
        "get_codex_capabilities",
        "get_codex_version"
    ],
    "supported_features": {
        "approval_modes": ["suggest", "auto-edit", "full-auto"],
        "sandboxed_execution": True,
        "mcp_extensions": True
    }
}



async def run_codex_command(
    args: list[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Run a codex CLI command and return the output.

    Args:
        args: Command line arguments for codex
        working_dir: Working directory for the command
        input_text: Optional input to send to stdin
        timeout: Timeout in seconds (default 5 minutes)

    Returns:
        Command output as string
    """
    cmd = ["codex"] + args
    logger.info(f"Running codex command: {' '.join(cmd)}")

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
            logger.warning(f"Codex returned non-zero exit code: {process.returncode}")
            if error:
                return f"Error (exit code {process.returncode}):\n{error}\n\nOutput:\n{output}"

        return output if output else error

    except FileNotFoundError:
        error_msg = "Codex CLI not found. Please install it with: npm install -g @openai/codex"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error running codex: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def codex_prompt(
    prompt: str,
    working_directory: str,
    model: Optional[str] = None,
) -> str:
    """
    Send a prompt to the OpenAI Codex CLI.

    BEST FOR: Small, focused code edits, quick bug fixes, one-shot tasks, simple refactors.
    NOT FOR: Complex algorithms (use claude), large refactoring (use aider), images (use gemini).

    Runs in suggest mode (default) where Codex proposes changes
    but requires approval.

    Args:
        prompt: The instruction or request for Codex
        working_directory: The directory to work in
        model: Optional model override (e.g., "o3", "o4-mini", "gpt-4.1")

    Returns:
        Codex's response
    """
    logger.info(f"codex_prompt called in {working_directory}")

    args = ["--quiet"]

    if model:
        args.extend(["--model", model])

    # Add the prompt as the final argument
    args.append(prompt)

    return await run_codex_command(args, working_dir=working_directory)


@mcp.tool()
async def codex_full_auto(
    prompt: str,
    working_directory: str,
    model: Optional[str] = None,
) -> str:
    """
    Run Codex in full-auto mode within a sandboxed environment.

    In full-auto mode, Codex can read, write, and execute commands
    automatically. It runs in a sandboxed, network-disabled environment
    scoped to the working directory.

    Args:
        prompt: The instruction or request for Codex
        working_directory: The directory to work in (sandbox scope)
        model: Optional model override

    Returns:
        Codex's response and actions taken
    """
    logger.info(f"codex_full_auto called in {working_directory}")

    args = ["--full-auto", "--quiet"]

    if model:
        args.extend(["--model", model])

    args.append(prompt)

    return await run_codex_command(args, working_dir=working_directory)


@mcp.tool()
async def codex_auto_edit(
    prompt: str,
    working_directory: str,
    model: Optional[str] = None,
) -> str:
    """
    Run Codex in auto-edit mode.

    In auto-edit mode, Codex can read and write files automatically
    but still asks permission before executing shell commands.

    Args:
        prompt: The instruction or request for Codex
        working_directory: The directory to work in
        model: Optional model override

    Returns:
        Codex's response and edits made
    """
    logger.info(f"codex_auto_edit called in {working_directory}")

    args = ["--approval-mode", "auto-edit", "--quiet"]

    if model:
        args.extend(["--model", model])

    args.append(prompt)

    return await run_codex_command(args, working_dir=working_directory)


@mcp.tool()
async def get_codex_version() -> str:
    """
    Get the version of the installed Codex CLI.

    Returns:
        Codex CLI version information
    """
    logger.info("get_codex_version called")
    return await run_codex_command(["--version"])


@mcp.tool()
async def get_codex_capabilities() -> str:
    """
    Get Codex's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Codex's capabilities,
    strengths, available tools, and supported features.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_codex_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting OpenAI Codex MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: codex_prompt, codex_full_auto, codex_auto_edit")
    logger.info("Discovery: get_codex_capabilities, get_codex_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
