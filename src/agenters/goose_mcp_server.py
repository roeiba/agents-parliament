"""
Goose MCP Server

An MCP server that allows other AI agents to interact with Block's
Goose AI agent.

Enhanced with:
- A2A capability discovery via agent cards
- Toolkits/extensions support
- Recipe-based workflow execution
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
logger = logging.getLogger("goose-mcp")

# Initialize FastMCP server
mcp = FastMCP("goose-agent")

# Agent Card for A2A Protocol capability discovery
AGENT_CARD = {
    "name": "goose-agent",
    "version": "2.1.0",
    "publisher": "Block (Square)",
    "description": "Best for autonomous multi-step workflows and CI/CD pipelines. Excels at chaining together complex task sequences without intervention.",
    "best_for": [
        "autonomous-workflows",
        "multi-step-pipelines",
        "ci-cd-integration",
        "build-test-deploy",
        "recipe-automation",
        "toolkit-integrations",
        "devops-tasks"
    ],
    "not_for": [
        "image-generation (use gemini)",
        "web-browsing (use gemini)",
        "complex-algorithms (use claude)",
        "simple-edits (use codex)",
        "git-focused-changes (use aider)"
    ],
    "strengths": [
        "autonomous-operation",
        "multi-step-workflows",
        "recipe-automation",
        "toolkit-extensibility",
        "error-recovery"
    ],
    "context_window": "varies",
    "priority": 5,  # Use for workflow automation, not single edits
    "tools": [
        "goose_run",
        "goose_run_file",
        "goose_run_recipe",
        "goose_with_toolkits",
        "get_goose_capabilities",
        "get_goose_version"
    ],
    "supported_features": {
        "recipes": True,
        "toolkits": True,
        "autonomous_execution": True,
        "mcp_extensions": True
    }
}



async def run_goose_command(
    args: list[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
    timeout: int = 600,
) -> str:
    """
    Run a goose CLI command and return the output.

    Args:
        args: Command line arguments for goose
        working_dir: Working directory for the command
        input_text: Optional input to send to stdin
        timeout: Timeout in seconds (default 10 minutes for complex tasks)

    Returns:
        Command output as string
    """
    cmd = ["goose"] + args
    logger.info(f"Running goose command: {' '.join(cmd)}")

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
            logger.warning(f"Goose returned non-zero exit code: {process.returncode}")
            if error:
                return f"Error (exit code {process.returncode}):\n{error}\n\nOutput:\n{output}"

        return output if output else error

    except FileNotFoundError:
        error_msg = "Goose CLI not found. Please install it from: https://github.com/block/goose"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error running goose: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def goose_run(
    instructions: str,
    working_directory: Optional[str] = None,
    system_instructions: Optional[str] = None,
) -> str:
    """
    Run Goose with text instructions.

    BEST FOR: Autonomous multi-step workflows, CI/CD pipelines, build-test-deploy, recipe automation.
    NOT FOR: Images (use gemini), complex algorithms (use claude), simple edits (use codex), git changes (use aider).

    Goose is an autonomous AI agent that can plan and execute
    multi-step workflows.

    Args:
        instructions: The task instructions for Goose
        working_directory: Optional directory to operate in
        system_instructions: Optional system instructions to customize behavior

    Returns:
        Goose's response and actions taken
    """
    logger.info(f"goose_run called")

    args = ["run", "--text", instructions]

    if system_instructions:
        args.extend(["--system", system_instructions])

    return await run_goose_command(args, working_dir=working_directory)


@mcp.tool()
async def goose_run_file(
    instructions_file: str,
    working_directory: Optional[str] = None,
    system_instructions: Optional[str] = None,
) -> str:
    """
    Run Goose with instructions from a file.

    Useful for complex, multi-step instructions that are easier
    to maintain in a file.

    Args:
        instructions_file: Path to a file containing instructions
        working_directory: Optional directory to operate in
        system_instructions: Optional system instructions

    Returns:
        Goose's response and actions taken
    """
    logger.info(f"goose_run_file called with {instructions_file}")

    args = ["run", "--instructions", instructions_file]

    if system_instructions:
        args.extend(["--system", system_instructions])

    return await run_goose_command(args, working_dir=working_directory)


@mcp.tool()
async def goose_run_recipe(
    recipe: str,
    working_directory: Optional[str] = None,
) -> str:
    """
    Run Goose with a predefined recipe.

    Recipes are reusable task templates that can be parameterized.

    Args:
        recipe: Name of the recipe file to run
        working_directory: Optional directory to operate in

    Returns:
        Goose's response and actions taken
    """
    logger.info(f"goose_run_recipe called with {recipe}")

    args = ["run", "--recipe", recipe]

    return await run_goose_command(args, working_dir=working_directory)


@mcp.tool()
async def get_goose_version() -> str:
    """
    Get the version of the installed Goose CLI.

    Returns:
        Goose version information
    """
    logger.info("get_goose_version called")
    return await run_goose_command(["--version"])


@mcp.tool()
async def get_goose_capabilities() -> str:
    """
    Get Goose's agent card for A2A protocol capability discovery.

    This returns a JSON agent card describing Goose's capabilities,
    strengths, available tools, and supported features. Useful for
    other agents to discover what Goose can do.

    Returns:
        JSON string containing the agent capability card
    """
    logger.info("get_goose_capabilities called")
    return json.dumps(AGENT_CARD, indent=2)


@mcp.tool()
async def goose_with_toolkits(
    instructions: str,
    toolkits: str,
    working_directory: Optional[str] = None,
    system_instructions: Optional[str] = None,
) -> str:
    """
    Run Goose with specific toolkits/extensions enabled.

    Toolkits extend Goose's capabilities with additional MCP servers
    or integrations (e.g., GitHub, Jira, databases).

    Args:
        instructions: The task instructions for Goose
        toolkits: Comma-separated list of toolkit names to enable
        working_directory: Optional directory to operate in
        system_instructions: Optional system instructions

    Returns:
        Goose's response and actions taken
    """
    logger.info(f"goose_with_toolkits called with toolkits={toolkits}")

    # Parse toolkit list
    toolkit_list = [t.strip() for t in toolkits.split(",") if t.strip()]

    args = ["run", "--text", instructions]

    # Add each toolkit
    for toolkit in toolkit_list:
        args.extend(["--toolkit", toolkit])

    if system_instructions:
        args.extend(["--system", system_instructions])

    return await run_goose_command(args, working_dir=working_directory)


def main():
    """Run the MCP server with STDIO transport."""
    logger.info("=" * 60)
    logger.info("Starting Goose MCP Server v2.0 (A2A Enhanced)")
    logger.info("=" * 60)
    logger.info("Core tools: goose_run, goose_run_file, goose_run_recipe")
    logger.info("Advanced tools: goose_with_toolkits")
    logger.info("Discovery: get_goose_capabilities, get_goose_version")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

