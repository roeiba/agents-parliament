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
    """Save config to file, creating directories if needed."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def get_mcp_server_config(agent: str) -> dict:
    """Get the MCP server configuration for an agent."""
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
        "args": []
    }


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
    """Smart provisioning command with interactive client and agent selection."""
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
    
    # Determine scope and get clients
    if args.scope == "global":
        # If --client is specified, use only that client
        if args.client:
            config_path = get_user_config_path(args.client)
            if not config_path:
                print_error(f"Unknown client: {args.client}")
                print_info(f"Available clients: {', '.join(AVAILABLE_CLIENTS.keys())}")
                return 1
            selected_clients = {args.client: config_path}
        else:
            # Auto-detect available clients and let user choose
            available_clients = get_available_clients()
            if not available_clients:
                print_error("No MCP clients detected on this system.")
                print_info("Install one of: Cursor, VS Code, Claude Desktop, Windsurf, or Antigravity")
                return 1
            
            selected_client_ids = prompt_client_selection(available_clients, args.yes)
            if not selected_client_ids:
                print_info("No clients selected. Exiting.")
                return 0
            
            selected_clients = {cid: available_clients[cid] for cid in selected_client_ids}
    else:
        # Project scope - use specified client or default to cursor
        project_dir = Path(args.project_dir or Path.cwd())
        if not project_dir.exists():
            print_error(f"Project directory does not exist: {project_dir}")
            return 1
        
        client = args.client or "cursor"
        config_path = get_project_config_path(project_dir, client)
        selected_clients = {client: config_path}
        print_info(f"Provisioning for project: {project_dir}")
    
    # Final confirmation
    if not args.yes and not args.dry_run:
        print()
        print_header("Confirm Provisioning")
        print(f"Agents: {', '.join(selected_agents)}")
        print(f"Clients: {', '.join(AVAILABLE_CLIENTS.get(c, c) for c in selected_clients.keys())}")
        
        # Check for missing CLIs in selection
        selected_missing = [a for a in selected_agents if a in missing]
        if selected_missing:
            print(f"\n{Colors.YELLOW}Note: {len(selected_missing)} agent(s) have uninstalled CLIs: {', '.join(selected_missing)}{Colors.ENDC}")
        print()
        
        confirm = input(f"{Colors.BOLD}Proceed? [Y/n]: {Colors.ENDC}").strip().lower()
        if confirm and confirm != 'y':
            print_info("Provisioning cancelled.")
            return 0
    
    # Provision to each selected client
    success_count = 0
    for client_id, config_path in selected_clients.items():
        client_name = AVAILABLE_CLIENTS.get(client_id, client_id)
        
        if args.dry_run:
            print()
            print_info(f"[DRY RUN] Would provision to {client_name}:")
            print(f"  Config: {config_path}")
            print(f"  Agents: {', '.join(selected_agents)}")
            success_count += 1
            continue
        
        # Load/create config
        config = load_config(config_path)
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Add agents
        for agent in selected_agents:
            mcp_name = f"{agent}-agent"
            config["mcpServers"][mcp_name] = get_mcp_server_config(agent)
        
        # Save
        save_config(config_path, config)
        print_success(f"Provisioned {len(selected_agents)} agent(s) to {client_name}")
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
    print_info(f"Successfully provisioned to {success_count} client(s).")
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
        default="project",
        help="User-level config (available to all projects)"
    )
    scope_group.add_argument(
        "--project", "-p",
        dest="scope",
        action="store_const",
        const="project",
        help="Project-level config (current directory)"
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
