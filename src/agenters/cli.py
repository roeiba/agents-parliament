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
    
    # Load existing config
    config = load_config(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Build new entries
    new_entries = {}
    for agent in agents:
        mcp_name = f"{agent}-agent"
        new_entries[mcp_name] = get_mcp_server_config(agent)
    
    if dry_run:
        print_header("Dry Run Preview")
        print(f"Config file: {config_path}")
        print(f"\nServers to add/update:")
        for name, cfg in new_entries.items():
            exists = "update" if name in config.get("mcpServers", {}) else "add"
            print(f"  • {name} [{exists}]")
            print(f"    command: {cfg['command']}")
        print(f"\n{Colors.YELLOW}No changes made (dry run){Colors.ENDC}")
        return True
    
    # Confirm if not --yes
    if not yes:
        print_header("Confirm Provisioning")
        print(f"Config file: {config_path}")
        print(f"Agents to provision: {', '.join(agents)}\n")
        
        confirm = input(f"{Colors.BOLD}Proceed? [Y/n]: {Colors.ENDC}").strip().lower()
        if confirm and confirm != 'y':
            print_info("Provisioning cancelled.")
            return False
    
    # Apply changes
    for name, cfg in new_entries.items():
        config["mcpServers"][name] = cfg
    
    # Save
    save_config(config_path, config)
    
    print_success(f"Provisioned {len(agents)} agent(s) to {config_path}")
    
    # Check for missing CLIs
    missing = []
    for agent in agents:
        cli_cmd = AGENT_CLI_COMMANDS.get(agent, agent)
        if not check_cli_installed(cli_cmd):
            missing.append(agent)
    
    if missing:
        print_warning(f"CLI tools not installed for: {', '.join(missing)}")
        print_info("The MCP servers will fail until the CLIs are installed.")
    
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
    """Smart provisioning command."""
    # Parse agents
    if args.agents:
        if args.agents.lower() == "all":
            agents = AVAILABLE_AGENTS.copy()
        else:
            agents = [a.strip() for a in args.agents.split(",")]
    else:
        # Default to all available agents
        agents = AVAILABLE_AGENTS.copy()
    
    # Determine scope and config path
    if args.scope == "global":
        client = args.client or "cursor"  # Default client
        config_path = get_user_config_path(client)
        if not config_path:
            print_error(f"Unknown client: {client}")
            print_info(f"Available clients: {', '.join(AVAILABLE_CLIENTS.keys())}")
            return 1
        print_info(f"Provisioning globally for {AVAILABLE_CLIENTS.get(client, client)}")
    else:
        # Project scope
        project_dir = Path(args.project_dir or Path.cwd())
        if not project_dir.exists():
            print_error(f"Project directory does not exist: {project_dir}")
            return 1
        
        client = args.client or "cursor"  # Default client
        config_path = get_project_config_path(project_dir, client)
        print_info(f"Provisioning for project: {project_dir}")
    
    # Provision
    success = provision_config(
        config_path=config_path,
        agents=agents,
        dry_run=args.dry_run,
        yes=args.yes
    )
    
    return 0 if success else 1


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
