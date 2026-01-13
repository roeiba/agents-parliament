#!/usr/bin/env python3
"""
Agenters CLI - Unified command-line interface for agents-parliament.

Provides subcommands for installing, uninstalling, and provisioning
MCP servers for AI agent cooperation.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Import existing installer/uninstaller logic
from . import install as installer_module
from . import uninstall as uninstaller_module


# ============================================================================
# Constants
# ============================================================================

AVAILABLE_AGENTS = ["claude", "aider", "codex", "gemini", "goose", "manus"]

AVAILABLE_CLIENTS = {
    "claude": "Claude Desktop",
    "cursor": "Cursor",
    "vscode": "VS Code",
    "windsurf": "Windsurf",
    "antigravity": "Antigravity (Gemini)",
}

# Agent CLI command mapping
AGENT_CLI_COMMANDS = {
    "claude": "claude",
    "aider": "aider",
    "codex": "codex",
    "gemini": "gemini",
    "goose": "goose",
    "manus": "manus",
}


# ============================================================================
# ANSI Colors (consistent with existing scripts)
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


# ============================================================================
# Config Path Helpers
# ============================================================================

def get_user_config_path(client: str) -> Optional[Path]:
    """Get user-level config path for a client."""
    paths = {
        "claude": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        "cursor": Path.home() / ".cursor" / "mcp.json",
        "vscode": Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "mcp.json",
        "windsurf": Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        "antigravity": Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
    }
    
    # Handle Windows paths
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        paths.update({
            "claude": Path(appdata) / "Claude" / "claude_desktop_config.json",
            "vscode": Path(appdata) / "Code" / "User" / "globalStorage" / "mcp.json",
        })
    # Handle Linux paths
    elif sys.platform == "linux":
        paths.update({
            "vscode": Path.home() / ".config" / "Code" / "User" / "globalStorage" / "mcp.json",
        })
    
    return paths.get(client)


def get_project_config_path(project_dir: Path, client: str) -> Path:
    """Get project-level config path for a client."""
    filenames = {
        "claude": ".mcp.json",  # Claude Code CLI uses .mcp.json at project root
        "cursor": ".cursor/mcp.json",
        "vscode": ".vscode/mcp.json",
        "windsurf": ".windsurf/mcp.json",
    }
    filename = filenames.get(client, "mcp.json")
    return project_dir / filename


def get_package_root() -> Path:
    """Get the root directory of this package."""
    return Path(__file__).parent.parent.parent.resolve()


def check_cli_installed(command: str) -> bool:
    """Check if a CLI tool is installed and available."""
    return shutil.which(command) is not None


def get_available_clients() -> dict[str, Path]:
    """Get MCP clients that are available on this system.
    
    A client is considered available if:
    - Its config file exists, OR
    - Its config parent directory exists (can be configured)
    
    Returns dict of client_id -> config_path for available clients.
    """
    available = {}
    for client_id in AVAILABLE_CLIENTS.keys():
        config_path = get_user_config_path(client_id)
        if config_path:
            # Check if config exists or parent dir exists (meaning the app is installed)
            if config_path.exists() or config_path.parent.exists():
                available[client_id] = config_path
    return available


def print_available_clients(available_clients: dict[str, Path]):
    """Print available MCP clients with their status."""
    print(f"\n{Colors.BOLD}Available MCP Clients:{Colors.ENDC}\n")
    for client_id, config_path in available_clients.items():
        client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
        if config_path.exists():
            print(f"  {Colors.GREEN}✓{Colors.ENDC} {client_name:20} {Colors.CYAN}(configured){Colors.ENDC}")
        else:
            print(f"  {Colors.YELLOW}○{Colors.ENDC} {client_name:20} {Colors.YELLOW}(not yet configured){Colors.ENDC}")
    print()


# ============================================================================
# Provisioning Logic
# ============================================================================

def load_config(config_path: Path) -> dict:
    """Load existing config or return empty structure."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_warning(f"Could not parse existing config, starting fresh.")
            return {"mcpServers": {}}
    return {"mcpServers": {}}


def save_config(config_path: Path, config: dict):
    """Save config to file, creating directories if needed.
    
    Creates a .backup file if the config already exists.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if file exists
    if config_path.exists():
        backup_path = config_path.with_suffix(config_path.suffix + ".backup")
        shutil.copy2(config_path, backup_path)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def get_mcp_server_config(agent: str) -> dict:
    """Get the MCP server configuration for an agent.
    
    Returns a professional MCP server config with:
    - command: The CLI command to run the MCP server
    - args: Command-line arguments (empty by default)
    - env: Environment variables (empty by default, user can add API keys etc.)
    - disabled: Whether the server is disabled (false by default)
    - transport: The transport mechanism (stdio for local process communication)
    """
    # Use the installed CLI commands from pyproject.toml entry points
    mcp_commands = {
        "claude": "claude-mcp",
        "aider": "aider-mcp",
        "codex": "codex-mcp",
        "gemini": "gemini-mcp",
        "goose": "goose-mcp",
        "manus": "manus-mcp",
    }
    return {
        "command": mcp_commands.get(agent, f"{agent}-mcp"),
        "args": [],
        "env": {},
        "disabled": False,
        "transport": "stdio"
    }


# ============================================================================
# Claude CLI Native Provisioning
# ============================================================================

def is_claude_cli_available() -> bool:
    """Check if Claude CLI is installed and supports mcp add-json."""
    if not check_cli_installed("claude"):
        return False
    try:
        result = subprocess.run(
            ["claude", "mcp", "add-json", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def run_claude_mcp_add(
    server_name: str,
    config: dict,
    scope: str,
    project_dir: Optional[Path] = None
) -> tuple[bool, str]:
    """Add an MCP server using Claude CLI.
    
    Args:
        server_name: Name for the MCP server (e.g., 'claude-agent')
        config: MCP server configuration dict
        scope: Either 'user' (global) or 'project' (project-level)
        project_dir: Project directory (required for project scope)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    config_json = json.dumps(config)
    cmd = ["claude", "mcp", "add-json", server_name, config_json, "--scope", scope]
    
    try:
        cwd = str(project_dir) if project_dir else None
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        if result.returncode == 0:
            return True, f"Added {server_name} to Claude ({scope})"
        else:
            error = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, f"Failed to add {server_name}: {error}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout adding {server_name}"
    except FileNotFoundError:
        return False, "Claude CLI not found"
    except OSError as e:
        return False, f"OS error: {e}"


def provision_claude_native(
    agents: list[str],
    scope: str,
    project_dir: Optional[Path] = None,
    dry_run: bool = False
) -> tuple[int, int]:
    """Provision MCP servers using native Claude CLI.
    
    Args:
        agents: List of agent names to provision
        scope: Either 'user' (global) or 'project' (project-level)
        project_dir: Project directory (required for project scope)
        dry_run: If True, only print commands without executing
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    for agent in agents:
        server_name = f"{agent}-agent"
        config = get_mcp_server_config(agent)
        
        if dry_run:
            config_json = json.dumps(config)
            cwd_info = f" (in {project_dir})" if project_dir else ""
            print(f"  {Colors.CYAN}[DRY RUN]{Colors.ENDC} Would run:")
            print(f"    claude mcp add-json {server_name} '{config_json}' --scope {scope}{cwd_info}")
            success_count += 1
            continue
        
        success, message = run_claude_mcp_add(server_name, config, scope, project_dir)
        if success:
            print_success(message)
            success_count += 1
        else:
            print_error(message)
            failure_count += 1
    
    return success_count, failure_count


def get_agent_cli_status(agents: list[str]) -> tuple[list[str], list[str]]:
    """Check CLI installation status for agents.
    
    Returns tuple of (installed_agents, missing_agents).
    """
    installed = []
    missing = []
    for agent in agents:
        cli_cmd = AGENT_CLI_COMMANDS.get(agent, agent)
        if check_cli_installed(cli_cmd):
            installed.append(agent)
        else:
            missing.append(agent)
    return installed, missing


def print_agent_status_table(installed: list[str], missing: list[str]):
    """Print a formatted table showing agent CLI installation status."""
    print(f"\n{Colors.BOLD}Agent CLI Status:{Colors.ENDC}\n")
    
    for agent in installed:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} {agent:12} {Colors.GREEN}installed{Colors.ENDC}")
    
    for agent in missing:
        print(f"  {Colors.YELLOW}○{Colors.ENDC} {agent:12} {Colors.YELLOW}not installed{Colors.ENDC}")
    
    print()


def get_installation_commands(agents: list[str]) -> dict[str, str]:
    """Get installation commands for agent CLIs."""
    commands = {
        "claude": "npm install -g @anthropic-ai/claude-code",
        "aider": "pip install aider-chat",
        "codex": "npm install -g @openai/codex",
        "gemini": "pip install google-generativeai",
        "goose": "curl -fsSL https://github.com/block/goose/releases/latest/download/install.sh | bash",
        "manus": "pip install manus-cli",
    }
    return {agent: commands.get(agent, f"# Install {agent} CLI") for agent in agents}


def prompt_agent_selection(installed: list[str], missing: list[str], yes: bool = False) -> list[str]:
    """Prompt user to select which agents to provision.
    
    Returns list of selected agents.
    """
    # Always show status table
    print_agent_status_table(installed, missing)
    
    # If --yes flag, use installed agents only (no prompts)
    if yes:
        if installed:
            print_info(f"Auto-selecting installed agents: {', '.join(installed)}")
        return installed if installed else []
    
    if not missing:
        # All requested agents are installed
        print_info("All agent CLIs are installed.")
        return installed
    
    if not installed:
        # No agents installed
        print_warning("None of the requested agent CLIs are installed.")
        print()
        print(f"{Colors.BOLD}Options:{Colors.ENDC}")
        print(f"  [1] Provision anyway (show install commands after)")
        print(f"  [2] Cancel provisioning")
        print()
        
        choice = input(f"{Colors.BOLD}Select option [1]: {Colors.ENDC}").strip() or "1"
        if choice == "2":
            return []
        return missing
    
    # Mix of installed and missing
    print(f"{Colors.BOLD}Options:{Colors.ENDC}")
    print(f"  [1] Provision only installed agents: {', '.join(installed)} {Colors.GREEN}(default){Colors.ENDC}")
    print(f"  [2] Provision all (will show install commands for missing)")
    print(f"  [3] Cancel")
    print()
    
    choice = input(f"{Colors.BOLD}Select option [1]: {Colors.ENDC}").strip() or "1"
    
    if choice == "1":
        return installed
    elif choice == "2":
        return installed + missing
    else:
        print_info("Provisioning cancelled.")
        return []


def prompt_client_selection(available_clients: dict[str, Path], yes: bool = False) -> list[str]:
    """Prompt user to select which MCP clients to provision to.
    
    Returns list of selected client IDs.
    """
    if not available_clients:
        print_error("No MCP clients detected on this system.")
        return []
    
    client_list = list(available_clients.keys())
    
    # If --yes flag or only one client, use all available
    if yes:
        return client_list
    
    print_available_clients(available_clients)
    
    if len(client_list) == 1:
        client_id = client_list[0]
        client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
        print_info(f"Only one client available: {client_name}")
        return client_list
    
    print(f"{Colors.BOLD}Select clients to provision (space-separated numbers, or 'all'):{Colors.ENDC}")
    print()
    
    for i, client_id in enumerate(client_list, 1):
        client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
        config_path = available_clients[client_id]
        status = f"{Colors.CYAN}configured{Colors.ENDC}" if config_path.exists() else f"{Colors.YELLOW}new{Colors.ENDC}"
        print(f"  [{i}] {client_name:20} ({status})")
    
    print()
    selection = input(f"{Colors.BOLD}Enter numbers (e.g., 1 2) or 'all' [all]: {Colors.ENDC}").strip() or "all"
    
    if selection.lower() == "all":
        return client_list
    
    try:
        indices = [int(x.strip()) for x in selection.split() if x.strip()]
        selected = [client_list[i-1] for i in indices if 1 <= i <= len(client_list)]
        if not selected:
            print_warning("No valid clients selected.")
            return []
        return selected
    except (ValueError, IndexError):
        print_error("Invalid selection.")
        return []


# prompt_specific_agent_selection removed - simplified agent selection flow


def print_installation_commands(agents: list[str]):
    """Print installation commands for missing agent CLIs."""
    commands = get_installation_commands(agents)
    
    print()
    print_header("Installation Commands")
    print("Run these commands to install the missing CLIs:\n")
    
    for agent in agents:
        cmd = commands.get(agent, f"# {agent}: check documentation")
        print(f"  {Colors.BOLD}{agent}:{Colors.ENDC}")
        print(f"    {Colors.CYAN}{cmd}{Colors.ENDC}")
        print()


def provision_config(
    config_path: Path,
    agents: list[str],
    dry_run: bool = False,
    yes: bool = False
) -> bool:
    """Provision MCP servers to a config file.
    
    Returns True if successful, False otherwise.
    """
    # Validate agents
    invalid_agents = [a for a in agents if a not in AVAILABLE_AGENTS]
    if invalid_agents:
        print_error(f"Invalid agents: {', '.join(invalid_agents)}")
        print_info(f"Available agents: {', '.join(AVAILABLE_AGENTS)}")
        return False
    
    # Check CLI installation status upfront
    installed, missing = get_agent_cli_status(agents)
    
    if dry_run:
        # For dry run, show what would happen
        print_agent_status_table(installed, missing)
        
        config = load_config(config_path)
        new_entries = {}
        for agent in agents:
            mcp_name = f"{agent}-agent"
            new_entries[mcp_name] = get_mcp_server_config(agent)
        
        print_header("Dry Run Preview")
        print(f"Config file: {config_path}")
        print(f"\nServers to add/update:")
        for name, cfg in new_entries.items():
            exists = "update" if name in config.get("mcpServers", {}) else "add"
            agent_name = name.replace("-agent", "")
            status = f"{Colors.GREEN}✓{Colors.ENDC}" if agent_name in installed else f"{Colors.YELLOW}○{Colors.ENDC}"
            print(f"  {status} {name} [{exists}]")
            print(f"    command: {cfg['command']}")
        
        if missing:
            print(f"\n{Colors.YELLOW}Warning: {len(missing)} agent(s) have missing CLIs{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}No changes made (dry run){Colors.ENDC}")
        return True
    
    # Interactive selection if not in --yes mode
    selected_agents = prompt_agent_selection(installed, missing, yes)
    
    if not selected_agents:
        print_info("No agents selected for provisioning.")
        return False
    
    # Final confirmation
    if not yes:
        print()
        print_header("Confirm Provisioning")
        print(f"Config file: {config_path}")
        print(f"Agents to provision: {', '.join(selected_agents)}")
        
        selected_installed = [a for a in selected_agents if a in installed]
        selected_missing = [a for a in selected_agents if a in missing]
        
        if selected_missing:
            print(f"\n{Colors.YELLOW}Note: {len(selected_missing)} agent(s) have uninstalled CLIs: {', '.join(selected_missing)}{Colors.ENDC}")
        print()
        
        confirm = input(f"{Colors.BOLD}Proceed? [Y/n]: {Colors.ENDC}").strip().lower()
        if confirm and confirm != 'y':
            print_info("Provisioning cancelled.")
            return False
    
    # Load existing config
    config = load_config(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Build and apply entries
    for agent in selected_agents:
        mcp_name = f"{agent}-agent"
        config["mcpServers"][mcp_name] = get_mcp_server_config(agent)
    
    # Save
    save_config(config_path, config)
    
    print_success(f"Provisioned {len(selected_agents)} agent(s) to {config_path}")
    
    # Show info about missing CLIs if any were provisioned
    provisioned_missing = [a for a in selected_agents if a in missing]
    if provisioned_missing:
        print()
        print_warning(f"CLI tools not installed for: {', '.join(provisioned_missing)}")
        print_info("These MCP servers will fail until the CLIs are installed.")
        print()
        show_cmds = input(f"{Colors.BOLD}Show installation commands? [y/N]: {Colors.ENDC}").strip().lower()
        if show_cmds == 'y':
            print_installation_commands(provisioned_missing)
    
    print_info("Restart your MCP client for changes to take effect.")
    return True


# ============================================================================
# Status Command
# ============================================================================

def cmd_status(args):
    """Show current configuration status."""
    print_header("Agenters Configuration Status")
    
    # Check which CLIs are installed
    print(f"{Colors.BOLD}Agent CLI Status:{Colors.ENDC}\n")
    for agent in AVAILABLE_AGENTS:
        cli_cmd = AGENT_CLI_COMMANDS.get(agent, agent)
        installed = check_cli_installed(cli_cmd)
        status = f"{Colors.GREEN}installed{Colors.ENDC}" if installed else f"{Colors.YELLOW}not found{Colors.ENDC}"
        print(f"  {agent:12} [{status}]")
    
    print()
    
    # Check client configs
    print(f"{Colors.BOLD}Client Configurations:{Colors.ENDC}\n")
    for client_id, client_name in AVAILABLE_CLIENTS.items():
        config_path = get_user_config_path(client_id)
        if config_path and config_path.exists():
            config = load_config(config_path)
            servers = config.get("mcpServers", {})
            agent_servers = [k for k in servers.keys() if k.endswith("-agent")]
            
            if agent_servers:
                print(f"  {Colors.GREEN}✓{Colors.ENDC} {client_name}")
                print(f"    Path: {config_path}")
                print(f"    Servers: {', '.join(agent_servers)}")
            else:
                print(f"  {Colors.YELLOW}○{Colors.ENDC} {client_name} (no agent servers)")
                print(f"    Path: {config_path}")
        else:
            print(f"  {Colors.CYAN}–{Colors.ENDC} {client_name} (not configured)")
            if config_path:
                print(f"    Path: {config_path}")
        print()
    
    # Check for project-level config
    cwd = Path.cwd()
    project_configs = [
        cwd / ".cursor" / "mcp.json",
        cwd / ".vscode" / "mcp.json",
        cwd / ".windsurf" / "mcp.json",
        cwd / "mcp.json",
        cwd / ".agenters.json",
    ]
    
    found_project = False
    for pc in project_configs:
        if pc.exists():
            if not found_project:
                print(f"{Colors.BOLD}Project-Level Configs (current directory):{Colors.ENDC}\n")
                found_project = True
            print(f"  {Colors.GREEN}✓{Colors.ENDC} {pc.name}")
            print(f"    Path: {pc}")
    
    if not found_project:
        print(f"{Colors.CYAN}No project-level configs in current directory.{Colors.ENDC}")


# ============================================================================
# Provision Command
# ============================================================================

def cmd_provision(args):
    """Smart provisioning command - provisions both global and project configs by default.
    
    Default behavior: provision to all detected global clients AND project-level clients.
    Use --global or --project flags to filter to just one scope.
    """
    # Parse agents
    if args.agents:
        if args.agents.lower() == "all":
            agents = AVAILABLE_AGENTS.copy()
        else:
            agents = [a.strip() for a in args.agents.split(",")]
    else:
        # Default to all available agents
        agents = AVAILABLE_AGENTS.copy()
    
    # Check CLI installation status upfront
    installed, missing = get_agent_cli_status(agents)
    
    # Agent selection (includes status display in interactive mode)
    selected_agents = prompt_agent_selection(installed, missing, args.yes)
    if not selected_agents:
        print_info("No agents selected. Exiting.")
        return 0
    
    # Determine project directory
    project_dir = Path(args.project_dir or Path.cwd())
    
    # Build list of all available targets based on scope filter
    all_targets = []  # List of (client_id, config_path, scope_label)
    
    include_global = args.scope in ("all", "global")
    include_project = args.scope in ("all", "project")
    
    # Global clients (user-level configs)
    if include_global:
        if args.client:
            # Specific client requested
            config_path = get_user_config_path(args.client)
            if config_path and (config_path.exists() or config_path.parent.exists()):
                all_targets.append((args.client, config_path, "global"))
        else:
            # Auto-detect all available global clients
            for client_id in AVAILABLE_CLIENTS.keys():
                config_path = get_user_config_path(client_id)
                if config_path and (config_path.exists() or config_path.parent.exists()):
                    all_targets.append((client_id, config_path, "global"))
    
    # Project clients (project-level configs)
    if include_project and project_dir.exists():
        project_capable_clients = ["claude", "cursor", "vscode", "windsurf"]
        if args.client and args.client in project_capable_clients:
            config_path = get_project_config_path(project_dir, args.client)
            all_targets.append((args.client, config_path, "project"))
        elif not args.client:
            for client_id in project_capable_clients:
                config_path = get_project_config_path(project_dir, client_id)
                all_targets.append((client_id, config_path, "project"))
    
    if not all_targets:
        print_error("No MCP clients available for provisioning.")
        print_info("Install one of: Cursor, VS Code, Claude Desktop, Windsurf, or Antigravity")
        return 1
    
    # Interactive client selection
    if args.yes:
        # Auto-mode: select all available targets
        selected_targets = all_targets
        print_info(f"Auto-selecting {len(selected_targets)} target(s)")
    else:
        print(f"\n{Colors.BOLD}Available MCP Client Targets:{Colors.ENDC}\n")
        
        for i, (client_id, config_path, scope) in enumerate(all_targets, 1):
            client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
            scope_tag = f"{Colors.BLUE}[global]{Colors.ENDC}" if scope == "global" else f"{Colors.CYAN}[project]{Colors.ENDC}"
            exists = config_path.exists()
            status = f"{Colors.GREEN}configured{Colors.ENDC}" if exists else f"{Colors.YELLOW}new{Colors.ENDC}"
            print(f"  [{i}] {client_name:15} {scope_tag} ({status})")
        
        print()
        selection = input(f"{Colors.BOLD}Enter numbers (e.g., 1 2 3), 'all', or 'q' to quit [all]: {Colors.ENDC}").strip() or "all"
        
        if selection.lower() == 'q':
            print_info("Provisioning cancelled.")
            return 0
        
        if selection.lower() == "all":
            selected_targets = all_targets
        else:
            try:
                indices = [int(x.strip()) for x in selection.split() if x.strip()]
                selected_targets = [all_targets[i-1] for i in indices if 1 <= i <= len(all_targets)]
                if not selected_targets:
                    print_warning("No valid targets selected.")
                    return 0
            except (ValueError, IndexError):
                print_error("Invalid selection.")
                return 1
    
    # Final confirmation
    if not args.yes and not args.dry_run:
        print()
        print_header("Confirm Provisioning")
        print(f"Agents: {', '.join(selected_agents)}")
        print(f"\nTargets ({len(selected_targets)}):")
        for client_id, config_path, scope in selected_targets:
            client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
            print(f"  • {client_name} [{scope}]: {config_path}")
        
        # Check for missing CLIs in selection
        selected_missing = [a for a in selected_agents if a in missing]
        if selected_missing:
            print(f"\n{Colors.YELLOW}Note: {len(selected_missing)} agent(s) have uninstalled CLIs: {', '.join(selected_missing)}{Colors.ENDC}")
        print()
        
        confirm = input(f"{Colors.BOLD}Proceed? [Y/n]: {Colors.ENDC}").strip().lower()
        if confirm and confirm != 'y':
            print_info("Provisioning cancelled.")
            return 0
    
    # Provision to each selected target
    success_count = 0
    failure_count = 0
    claude_cli_available = is_claude_cli_available()
    
    for client_id, config_path, scope in selected_targets:
        client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
        scope_tag = f"[{scope}]"
        
        if args.dry_run:
            # Check if we'll use native Claude CLI
            use_native = (
                client_id == "claude" 
                and claude_cli_available 
                and getattr(args, 'method', 'auto') != 'file'
            )
            print()
            if use_native:
                print_info(f"[DRY RUN] Would provision to {client_name} {scope_tag} via Claude CLI:")
                claude_scope = "user" if scope == "global" else "project"
                provision_claude_native(
                    agents=selected_agents,
                    scope=claude_scope,
                    project_dir=project_dir if scope == "project" else None,
                    dry_run=True
                )
            else:
                print_info(f"[DRY RUN] Would provision to {client_name} {scope_tag}:")
                print(f"  Config: {config_path}")
                print(f"  Agents: {', '.join(selected_agents)}")
            success_count += 1
            continue
        
        # Check if we should use native Claude CLI for this target
        use_native = (
            client_id == "claude" 
            and claude_cli_available 
            and getattr(args, 'method', 'auto') != 'file'
        )
        force_native = getattr(args, 'method', 'auto') == 'native'
        
        if client_id == "claude" and force_native and not claude_cli_available:
            print_error(f"--native specified but Claude CLI not available")
            failure_count += 1
            continue
        
        if use_native:
            # Use native Claude CLI
            claude_scope = "user" if scope == "global" else "project"
            print_info(f"Provisioning to {client_name} {scope_tag} via Claude CLI...")
            successes, failures = provision_claude_native(
                agents=selected_agents,
                scope=claude_scope,
                project_dir=project_dir if scope == "project" else None,
                dry_run=False
            )
            if failures == 0:
                success_count += 1
            else:
                failure_count += 1
        else:
            # Fallback: write config file directly
            if client_id == "claude" and not claude_cli_available:
                print_warning(f"Claude CLI not available, using file-based provisioning")
            
            config = load_config(config_path)
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            
            for agent in selected_agents:
                mcp_name = f"{agent}-agent"
                config["mcpServers"][mcp_name] = get_mcp_server_config(agent)
            
            save_config(config_path, config)
            print_success(f"Provisioned {len(selected_agents)} agent(s) to {client_name} {scope_tag}")
            success_count += 1
    
    if args.dry_run:
        print(f"\n{Colors.YELLOW}No changes made (dry run){Colors.ENDC}")
        return 0
    
    # Show info about missing CLIs if any were provisioned
    provisioned_missing = [a for a in selected_agents if a in missing]
    if provisioned_missing:
        print()
        print_warning(f"CLI tools not installed for: {', '.join(provisioned_missing)}")
        print_info("These MCP servers will fail until the CLIs are installed.")
        if not args.yes:
            print()
            show_cmds = input(f"{Colors.BOLD}Show installation commands? [y/N]: {Colors.ENDC}").strip().lower()
            if show_cmds == 'y':
                print_installation_commands(provisioned_missing)
    
    print()
    print_info(f"Successfully provisioned to {success_count} target(s).")
    print_info("Restart your MCP client(s) for changes to take effect.")
    return 0


# ============================================================================
# Install/Uninstall Commands (wrappers)
# ============================================================================

def cmd_install(args):
    """Interactive installer (wraps existing install.py)."""
    # Pass through to existing installer
    sys.argv = ["agenters-install"]
    if args.all:
        sys.argv.append("--all")
    installer_module.main()


def cmd_uninstall(args):
    """Interactive uninstaller (wraps existing uninstall.py)."""
    # Pass through to existing uninstaller
    sys.argv = ["agenters-uninstall"]
    uninstaller_module.main()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="agenters",
        description="Agenters: MCP servers for AI agent cooperation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agenters status                              # Show configuration status
  agenters provision --global --client cursor  # Provision globally for Cursor
  agenters provision --project --agents claude,aider  # Provision for project
  agenters install                             # Interactive installer
  agenters uninstall                           # Interactive uninstaller
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show current configuration status"
    )
    status_parser.set_defaults(func=cmd_status)
    
    # Provision command
    provision_parser = subparsers.add_parser(
        "provision",
        help="Provision MCP servers"
    )
    scope_group = provision_parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--global", "-g",
        dest="scope",
        action="store_const",
        const="global",
        default="all",
        help="Only user-level configs (filter)"
    )
    scope_group.add_argument(
        "--project", "-p",
        dest="scope",
        action="store_const",
        const="project",
        help="Only project-level configs (filter)"
    )
    provision_parser.add_argument(
        "--client", "-c",
        choices=list(AVAILABLE_CLIENTS.keys()),
        help="Target MCP client (default: cursor)"
    )
    provision_parser.add_argument(
        "--agents", "-a",
        metavar="LIST",
        help="Comma-separated agents or 'all' (default: all)"
    )
    provision_parser.add_argument(
        "--project-dir",
        metavar="DIR",
        help="Project directory (default: current directory)"
    )
    provision_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )
    provision_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Non-interactive mode (skip confirmations)"
    )
    method_group = provision_parser.add_mutually_exclusive_group()
    method_group.add_argument(
        "--native",
        dest="method",
        action="store_const",
        const="native",
        default="auto",
        help="Force native Claude CLI provisioning (bypasses interactive approval)"
    )
    method_group.add_argument(
        "--file",
        dest="method",
        action="store_const",
        const="file",
        help="Force file-based provisioning (writes .mcp.json directly)"
    )
    provision_parser.set_defaults(func=cmd_provision)
    
    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Interactive MCP server installer"
    )
    install_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Include all servers, even without installed CLIs"
    )
    install_parser.set_defaults(func=cmd_install)
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Interactive MCP server uninstaller"
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
