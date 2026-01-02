#!/usr/bin/env python3
"""
Cooperating Agents MCP Installer

An interactive installer that allows users to select which MCP servers
to install and configure them in their preferred MCP client config.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# ANSI colors for terminal output
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

# Available MCP servers
SERVERS = {
    "claude": {
        "name": "Claude Code",
        "description": "Anthropic's Claude Code via claude-agent-sdk",
        "file": "claude_mcp_server.py",
        "mcp_name": "claude-agent",
        "prerequisite": "Claude Code CLI (claude)",
        "install_cmd": "See https://docs.anthropic.com/en/docs/claude-code",
    },
    "aider": {
        "name": "Aider",
        "description": "AI pair programming tool with Git integration",
        "file": "aider_mcp_server.py",
        "mcp_name": "aider-agent",
        "prerequisite": "Aider CLI (aider)",
        "install_cmd": "pip install aider-chat",
    },
    "codex": {
        "name": "OpenAI Codex",
        "description": "OpenAI's Codex CLI for code generation",
        "file": "codex_mcp_server.py",
        "mcp_name": "codex-agent",
        "prerequisite": "Codex CLI (codex)",
        "install_cmd": "npm install -g @openai/codex",
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google's Gemini CLI with large context window",
        "file": "gemini_mcp_server.py",
        "mcp_name": "gemini-agent",
        "prerequisite": "Gemini CLI (gemini)",
        "install_cmd": "npm install -g @google/gemini-cli",
    },
    "goose": {
        "name": "Goose (Block)",
        "description": "Block's autonomous AI agent",
        "file": "goose_mcp_server.py",
        "mcp_name": "goose-agent",
        "prerequisite": "Goose CLI (goose)",
        "install_cmd": "curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash",
    },
}

# Known MCP config locations - organized by scope
USER_LEVEL_CONFIGS = {
    "claude_desktop": {
        "name": "Claude Desktop",
        "path": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        "path_windows": Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
    },
    "cursor_global": {
        "name": "Cursor (Global)",
        "path": Path.home() / ".cursor" / "mcp.json",
    },
    "windsurf": {
        "name": "Windsurf",
        "path": Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        "path_linux": Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
    },
    "antigravity": {
        "name": "Antigravity (Gemini)",
        "path": Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
    },
    "vscode_global": {
        "name": "VS Code (Global)",
        "path": Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "mcp.json",
        "path_windows": Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "mcp.json",
        "path_linux": Path.home() / ".config" / "Code" / "User" / "globalStorage" / "mcp.json",
    },
    "custom_user": {
        "name": "Custom user-level location",
        "path": None,
    },
}

PROJECT_LEVEL_CONFIGS = {
    "cursor_project": {
        "name": "Cursor (Project)",
        "filename": ".cursor/mcp.json",
    },
    "vscode_project": {
        "name": "VS Code (Project)",
        "filename": ".vscode/mcp.json",
    },
    "windsurf_project": {
        "name": "Windsurf (Project)",
        "filename": ".windsurf/mcp.json",
    },
    "mcp_json": {
        "name": "Project root (mcp.json)",
        "filename": "mcp.json",
    },
    "custom_project": {
        "name": "Custom project location",
        "filename": None,
    },
}



def get_project_root() -> Path:
    """Get the root directory of this project."""
    return Path(__file__).parent.resolve()


def check_cli_installed(command: str) -> bool:
    """Check if a CLI tool is installed and available."""
    return shutil.which(command) is not None


def display_server_menu(include_all: bool = False) -> list[str]:
    """Display server selection menu and return selected servers.
    
    Args:
        include_all: If True, show all servers. If False, only show servers
                     with installed CLIs.
    """
    print_header("Select MCP Servers to Install")
    
    # Build list of available servers
    available_servers = []
    for key, server in SERVERS.items():
        cli_cmd = server["prerequisite"].split("(")[1].rstrip(")")
        installed = check_cli_installed(cli_cmd)
        available_servers.append((key, server, installed))
    
    # Filter to only installed if not include_all
    if not include_all:
        displayable = [(k, s, i) for k, s, i in available_servers if i]
        if not displayable:
            print_warning("No MCP servers have their CLI tools installed.")
            print_info("Run with --all flag to configure servers anyway.")
            print()
            for key, server, _ in available_servers:
                print(f"  • {server['name']}: {server['install_cmd']}")
            sys.exit(1)
    else:
        displayable = available_servers
    
    print("Available servers:\n")
    for i, (key, server, installed) in enumerate(displayable, 1):
        status = f"{Colors.GREEN}[installed]{Colors.ENDC}" if installed else f"{Colors.YELLOW}[not found]{Colors.ENDC}"
        
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {server['name']} {status}")
        print(f"     {Colors.CYAN}{server['description']}{Colors.ENDC}")
        print(f"     Requires: {server['prerequisite']}")
        print()
    
    # Only show "Select ALL" option
    installed_keys = [k for k, s, i in displayable if i]
    print(f"  {Colors.BOLD}A.{Colors.ENDC} Select ALL {'servers' if include_all else 'installed servers'}")
    print(f"  {Colors.BOLD}Q.{Colors.ENDC} Quit\n")
    
    if not include_all:
        print_info(f"Tip: Run with --all to also configure servers without installed CLIs.\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (comma-separated numbers, A for all, Q to quit): {Colors.ENDC}").strip()
        
        if selection.upper() == 'Q':
            print_info("Installation cancelled.")
            sys.exit(0)
        
        if selection.upper() == 'A':
            return [k for k, s, i in displayable]
        
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(displayable):
                    selected.append(displayable[idx - 1][0])
                else:
                    raise ValueError(f"Invalid index: {idx}")
            if selected:
                return selected
        except ValueError as e:
            print_error(f"Invalid selection: {e}. Please try again.")


def display_scope_menu() -> str:
    """Display scope selection menu (user vs project level)."""
    print_header("Select Installation Scope")
    
    print("Where should the MCP servers be available?\n")
    print(f"  {Colors.BOLD}1.{Colors.ENDC} User-level (global)")
    print(f"     {Colors.CYAN}Available to all projects for a specific MCP client{Colors.ENDC}\n")
    print(f"  {Colors.BOLD}2.{Colors.ENDC} Project-level")
    print(f"     {Colors.CYAN}Available only in a specific project directory{Colors.ENDC}\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (1 or 2): {Colors.ENDC}").strip()
        if selection == "1":
            return "user"
        elif selection == "2":
            return "project"
        print_error("Invalid selection. Please enter 1 or 2.")


def display_user_config_menu() -> Path:
    """Display user-level config location menu."""
    print_header("Select User-Level Configuration")
    
    print("Select the MCP client to configure:\n")
    
    valid_options = []
    for i, (key, config) in enumerate(USER_LEVEL_CONFIGS.items(), 1):
        path = config.get("path_windows") if sys.platform == "win32" else config.get("path")
        
        if path is None:
            status = ""
        elif path.exists():
            status = f"{Colors.GREEN}[exists]{Colors.ENDC}"
        else:
            status = f"{Colors.YELLOW}[will create]{Colors.ENDC}"
        
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {config['name']} {status}")
        if path:
            print(f"     {Colors.CYAN}{path}{Colors.ENDC}")
        print()
        valid_options.append((key, path))
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (1-{len(valid_options)}): {Colors.ENDC}").strip()
        
        try:
            idx = int(selection)
            if 1 <= idx <= len(valid_options):
                key, path = valid_options[idx - 1]
                
                if key == "custom_user":
                    custom_path = input(f"{Colors.BOLD}Enter the full path to your config file: {Colors.ENDC}").strip()
                    return Path(custom_path).expanduser()
                
                return path
        except ValueError:
            pass
        
        print_error("Invalid selection. Please try again.")


def display_project_config_menu() -> Path:
    """Display project-level config location menu."""
    print_header("Select Project Configuration")
    
    # Get project directory
    print("Enter the project directory where you want to install the MCP servers.\n")
    default_cwd = Path.cwd()
    project_dir_input = input(f"{Colors.BOLD}Project directory [{default_cwd}]: {Colors.ENDC}").strip()
    project_dir = Path(project_dir_input).expanduser() if project_dir_input else default_cwd
    
    if not project_dir.exists():
        print_error(f"Directory does not exist: {project_dir}")
        create = input(f"{Colors.BOLD}Create it? [y/N]: {Colors.ENDC}").strip().lower()
        if create == 'y':
            project_dir.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {project_dir}")
        else:
            print_info("Installation cancelled.")
            sys.exit(0)
    
    print(f"\n{Colors.CYAN}Project: {project_dir}{Colors.ENDC}\n")
    print("Select config file location:\n")
    
    valid_options = []
    for i, (key, config) in enumerate(PROJECT_LEVEL_CONFIGS.items(), 1):
        filename = config.get("filename")
        
        if filename:
            full_path = project_dir / filename
            if full_path.exists():
                status = f"{Colors.GREEN}[exists]{Colors.ENDC}"
            else:
                status = f"{Colors.YELLOW}[will create]{Colors.ENDC}"
        else:
            full_path = None
            status = ""
        
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {config['name']} {status}")
        if filename:
            print(f"     {Colors.CYAN}{full_path}{Colors.ENDC}")
        print()
        valid_options.append((key, full_path, project_dir))
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (1-{len(valid_options)}): {Colors.ENDC}").strip()
        
        try:
            idx = int(selection)
            if 1 <= idx <= len(valid_options):
                key, path, proj_dir = valid_options[idx - 1]
                
                if key == "custom_project":
                    custom_filename = input(f"{Colors.BOLD}Enter the config filename (relative to project): {Colors.ENDC}").strip()
                    return proj_dir / custom_filename
                
                return path
        except ValueError:
            pass
        
        print_error("Invalid selection. Please try again.")


def display_config_menu() -> Path:
    """Display config location menu and return selected path."""
    scope = display_scope_menu()
    
    if scope == "user":
        return display_user_config_menu()
    else:
        return display_project_config_menu()



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


def create_backup(config_path: Path) -> Path | None:
    """Create a backup of the config file if it exists.
    
    Returns the backup path if created, None otherwise.
    """
    if not config_path.exists():
        return None
    
    # Create backup with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup_{timestamp}.json")
    
    try:
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception as e:
        print_warning(f"Could not create backup: {e}")
        return None


def save_config(config_path: Path, config: dict):
    """Save config to file, creating directories if needed."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def install_servers(selected_servers: list[str], config_path: Path):
    """Install selected servers to the config file."""
    print_header("Installing MCP Servers")
    
    project_root = get_project_root()
    src_dir = project_root / "src"
    
    # Create backup if file exists
    backup_path = create_backup(config_path)
    if backup_path:
        print_success(f"Created backup: {backup_path}")
    
    # Load existing config (merge, don't overwrite)
    config = load_config(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    installed = []
    skipped = []
    
    for server_key in selected_servers:
        server = SERVERS[server_key]
        server_file = src_dir / server["file"]
        
        if not server_file.exists():
            print_error(f"{server['name']}: Server file not found at {server_file}")
            skipped.append(server_key)
            continue
        
        # Check if already configured
        if server["mcp_name"] in config["mcpServers"]:
            print_warning(f"{server['name']}: Already configured, updating...")
        
        # Add server config
        config["mcpServers"][server["mcp_name"]] = {
            "command": "python",
            "args": [str(server_file)]
        }
        
        print_success(f"{server['name']}: Configured as '{server['mcp_name']}'")
        installed.append(server_key)
    
    # Save config
    save_config(config_path, config)
    
    print_header("Installation Summary")
    
    if installed:
        print(f"{Colors.GREEN}Successfully installed:{Colors.ENDC}")
        for key in installed:
            print(f"  • {SERVERS[key]['name']}")
        print()
    
    if skipped:
        print(f"{Colors.YELLOW}Skipped (errors):{Colors.ENDC}")
        for key in skipped:
            print(f"  • {SERVERS[key]['name']}")
        print()
    
    print(f"{Colors.CYAN}Configuration saved to:{Colors.ENDC}")
    print(f"  {config_path}\n")
    
    # Check for missing CLIs
    missing_clis = []
    for key in installed:
        server = SERVERS[key]
        cli_cmd = server["prerequisite"].split("(")[1].rstrip(")")
        if not check_cli_installed(cli_cmd):
            missing_clis.append((server["name"], server["install_cmd"]))
    
    if missing_clis:
        print_warning("The following CLI tools are not installed:")
        print()
        for name, cmd in missing_clis:
            print(f"  {Colors.BOLD}{name}:{Colors.ENDC}")
            print(f"    {Colors.CYAN}{cmd}{Colors.ENDC}")
            print()
    
    print_info("Restart your MCP client for changes to take effect.")


def main():
    """Main installer entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Install MCP servers for AI agent cooperation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py          # Only show servers with installed CLIs
  python install.py --all    # Show all servers, even without installed CLIs
        """
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="include_all",
        help="Include all servers, even those without installed CLI tools"
    )
    args = parser.parse_args()
    
    print_header("Cooperating Agents MCP Installer")
    
    print("This installer will help you configure MCP servers")
    print("to enable AI agents to interact with each other.\n")
    
    # Check we're in the right directory
    project_root = get_project_root()
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print_error(f"Source directory not found: {src_dir}")
        print_info("Please run this installer from the project root.")
        sys.exit(1)
    
    # Step 1: Select servers
    selected_servers = display_server_menu(include_all=args.include_all)
    print_success(f"Selected {len(selected_servers)} server(s): {', '.join(selected_servers)}")
    
    # Step 2: Select config location
    config_path = display_config_menu()
    print_success(f"Config location: {config_path}")
    
    # Step 3: Confirm
    print_header("Confirm Installation")
    print(f"Servers to install: {', '.join(SERVERS[s]['name'] for s in selected_servers)}")
    print(f"Config file: {config_path}\n")
    
    confirm = input(f"{Colors.BOLD}Proceed with installation? [Y/n]: {Colors.ENDC}").strip().lower()
    if confirm and confirm != 'y':
        print_info("Installation cancelled.")
        sys.exit(0)
    
    # Step 4: Install
    install_servers(selected_servers, config_path)


if __name__ == "__main__":
    main()

