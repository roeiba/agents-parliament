#!/usr/bin/env python3
"""
Cooperating Agents MCP Uninstaller

An interactive uninstaller that removes MCP servers from config files
and optionally restores from backup.
"""

import argparse
import json
import os
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

# MCP server names that we manage
MANAGED_SERVERS = {
    "claude-agent": "Claude Code",
    "aider-agent": "Aider",
    "codex-agent": "OpenAI Codex",
    "gemini-agent": "Google Gemini",
    "goose-agent": "Goose (Block)",
}

# Known MCP config locations
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
    "custom": {
        "name": "Custom location",
        "path": None,
    },
}


def find_backups(config_path: Path) -> list[Path]:
    """Find all backup files for the given config path."""
    if not config_path.parent.exists():
        return []
    
    # Look for files matching the backup pattern
    pattern = config_path.stem + ".backup_*.json"
    backups = list(config_path.parent.glob(pattern))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return backups


def load_config(config_path: Path) -> dict:
    """Load existing config or return empty structure."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_warning(f"Could not parse config file.")
            return {"mcpServers": {}}
    return {"mcpServers": {}}


def save_config(config_path: Path, config: dict):
    """Save config to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def display_config_menu() -> Path:
    """Display config location menu and return selected path."""
    print_header("Select Configuration to Modify")
    
    print("Select the MCP client config to modify:\n")
    
    valid_options = []
    for i, (key, config) in enumerate(USER_LEVEL_CONFIGS.items(), 1):
        path = config.get("path_windows") if sys.platform == "win32" else config.get("path")
        
        if path is None:
            status = ""
        elif path.exists():
            status = f"{Colors.GREEN}[exists]{Colors.ENDC}"
        else:
            status = f"{Colors.YELLOW}[not found]{Colors.ENDC}"
        
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
                
                if key == "custom":
                    custom_path = input(f"{Colors.BOLD}Enter the full path to your config file: {Colors.ENDC}").strip()
                    return Path(custom_path).expanduser()
                
                return path
        except ValueError:
            pass
        
        print_error("Invalid selection. Please try again.")


def display_server_removal_menu(config: dict) -> list[str]:
    """Display menu to select which servers to remove."""
    print_header("Select Servers to Remove")
    
    mcp_servers = config.get("mcpServers", {})
    
    # Find managed servers in config
    found_servers = []
    for mcp_name, display_name in MANAGED_SERVERS.items():
        if mcp_name in mcp_servers:
            found_servers.append((mcp_name, display_name))
    
    if not found_servers:
        print_warning("No Cooperating Agents MCP servers found in this config.")
        return []
    
    print("The following managed servers are installed:\n")
    for i, (mcp_name, display_name) in enumerate(found_servers, 1):
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {display_name} ({mcp_name})")
    print()
    
    print(f"  {Colors.BOLD}A.{Colors.ENDC} Remove ALL managed servers")
    print(f"  {Colors.BOLD}Q.{Colors.ENDC} Cancel\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (comma-separated numbers, A for all, Q to cancel): {Colors.ENDC}").strip()
        
        if selection.upper() == 'Q':
            return []
        
        if selection.upper() == 'A':
            return [name for name, _ in found_servers]
        
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(found_servers):
                    selected.append(found_servers[idx - 1][0])
                else:
                    raise ValueError(f"Invalid index: {idx}")
            if selected:
                return selected
        except ValueError as e:
            print_error(f"Invalid selection: {e}. Please try again.")


def display_backup_menu(backups: list[Path]) -> Path | None:
    """Display backup selection menu."""
    print_header("Restore from Backup")
    
    print("Available backups (newest first):\n")
    
    for i, backup in enumerate(backups[:10], 1):  # Show max 10 backups
        # Extract timestamp from filename
        try:
            timestamp_part = backup.stem.split("backup_")[1]
            from datetime import datetime
            dt = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (IndexError, ValueError):
            formatted_time = "Unknown date"
        
        size_kb = backup.stat().st_size / 1024
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {formatted_time} ({size_kb:.1f} KB)")
        print(f"     {Colors.CYAN}{backup.name}{Colors.ENDC}")
        print()
    
    print(f"  {Colors.BOLD}N.{Colors.ENDC} Don't restore, just remove servers")
    print(f"  {Colors.BOLD}Q.{Colors.ENDC} Cancel\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection: {Colors.ENDC}").strip()
        
        if selection.upper() == 'Q':
            return None
        
        if selection.upper() == 'N':
            return Path("NO_RESTORE")  # Special marker
        
        try:
            idx = int(selection)
            if 1 <= idx <= min(10, len(backups)):
                return backups[idx - 1]
        except ValueError:
            pass
        
        print_error("Invalid selection. Please try again.")


def restore_from_backup(config_path: Path, backup_path: Path):
    """Restore config from backup file."""
    import shutil
    
    try:
        shutil.copy2(backup_path, config_path)
        print_success(f"Restored from backup: {backup_path.name}")
        return True
    except Exception as e:
        print_error(f"Failed to restore from backup: {e}")
        return False


def remove_servers(config_path: Path, servers_to_remove: list[str]):
    """Remove specified servers from config."""
    config = load_config(config_path)
    
    removed = []
    for server in servers_to_remove:
        if server in config.get("mcpServers", {}):
            del config["mcpServers"][server]
            removed.append(server)
            print_success(f"Removed: {MANAGED_SERVERS.get(server, server)}")
    
    if removed:
        save_config(config_path, config)
        print()
        print_success(f"Configuration updated: {config_path}")
    
    return removed


def main():
    """Main uninstaller entry point."""
    parser = argparse.ArgumentParser(
        description="Uninstall MCP servers or restore from backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python uninstall.py              # Interactive uninstall
  python uninstall.py --restore    # Jump directly to backup restore
        """
    )
    parser.add_argument(
        "--restore", "-r",
        action="store_true",
        help="Skip removal and go directly to backup restoration"
    )
    args = parser.parse_args()
    
    print_header("Cooperating Agents MCP Uninstaller")
    
    print("This uninstaller will help you remove MCP servers")
    print("or restore your configuration from a backup.\n")
    
    # Step 1: Select config file
    config_path = display_config_menu()
    
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    print_success(f"Config location: {config_path}")
    
    # Check for backups
    backups = find_backups(config_path)
    
    if args.restore:
        # Jump directly to backup restore
        if not backups:
            print_warning("No backups found for this config file.")
            sys.exit(1)
        
        backup_to_restore = display_backup_menu(backups)
        if backup_to_restore and backup_to_restore != Path("NO_RESTORE"):
            if restore_from_backup(config_path, backup_to_restore):
                print_info("Restart your MCP client for changes to take effect.")
        else:
            print_info("No restore performed.")
        return
    
    # Step 2: Load config and show removal options
    config = load_config(config_path)
    servers_to_remove = display_server_removal_menu(config)
    
    if not servers_to_remove:
        print_info("No servers selected for removal.")
        sys.exit(0)
    
    # Step 3: Ask about backup restoration
    if backups:
        print()
        print_info(f"Found {len(backups)} backup(s) for this config file.")
        use_backup = input(f"{Colors.BOLD}Would you like to restore from a backup instead? [y/N]: {Colors.ENDC}").strip().lower()
        
        if use_backup == 'y':
            backup_to_restore = display_backup_menu(backups)
            if backup_to_restore and backup_to_restore != Path("NO_RESTORE"):
                # Confirm restore
                print_header("Confirm Restore")
                print(f"This will replace your current config with the backup.")
                print(f"Backup: {backup_to_restore.name}\n")
                
                confirm = input(f"{Colors.BOLD}Proceed with restore? [Y/n]: {Colors.ENDC}").strip().lower()
                if confirm and confirm != 'y':
                    print_info("Restore cancelled.")
                    sys.exit(0)
                
                if restore_from_backup(config_path, backup_to_restore):
                    print_info("Restart your MCP client for changes to take effect.")
                return
    
    # Step 4: Confirm removal
    print_header("Confirm Removal")
    print(f"Servers to remove:")
    for server in servers_to_remove:
        print(f"  • {MANAGED_SERVERS.get(server, server)}")
    print(f"\nConfig file: {config_path}\n")
    
    confirm = input(f"{Colors.BOLD}Proceed with removal? [Y/n]: {Colors.ENDC}").strip().lower()
    if confirm and confirm != 'y':
        print_info("Removal cancelled.")
        sys.exit(0)
    
    # Step 5: Remove servers
    print_header("Removing Servers")
    removed = remove_servers(config_path, servers_to_remove)
    
    print_header("Uninstall Summary")
    
    if removed:
        print(f"{Colors.GREEN}Successfully removed:{Colors.ENDC}")
        for server in removed:
            print(f"  • {MANAGED_SERVERS.get(server, server)}")
        print()
    
    print_info("Restart your MCP client for changes to take effect.")


if __name__ == "__main__":
    main()
