"""
Google Gemini CLI MCP Server

An MCP server that allows other AI agents to interact with the
Google Gemini CLI.
"""

import asyncio
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
logger = logging.getLogger("gemini-mcp")

# Initialize FastMCP server
mcp = FastMCP("gemini-agent")


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


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Google Gemini MCP Server")
    logger.info("=" * 60)
    logger.info("Tools: gemini_prompt, gemini_in_directory, gemini_with_search, get_gemini_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
