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


# ============================================================================
# ANSI Colors
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
# Server Definitions
# ============================================================================

MANAGED_SERVERS = {
    "claude-agent": "Claude Code",
    "aider-agent": "Aider",
    "codex-agent": "OpenAI Codex",
    "gemini-agent": "Google Gemini",
    "goose-agent": "Goose (Block)",
    "manus-agent": "Manus",
}


# ============================================================================
# Config Locations
# ============================================================================

CONFIG_LOCATIONS = {
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
    "custom": {
        "name": "Custom location",
        "path": None,
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def find_backups(config_path: Path) -> list[Path]:
    """Find all backup files for the given config path."""
    if not config_path.parent.exists():
        return []
    
    pattern = config_path.stem + ".backup_*"
    backups = list(config_path.parent.glob(pattern))
    return sorted(backups, reverse=True)


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
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def display_config_menu() -> Path:
    """Display config location menu and return selected path."""
    print_header("Select Configuration to Modify")
    
    print("Select the MCP client configuration:\n")
    
    valid_options = []
    for i, (key, config) in enumerate(CONFIG_LOCATIONS.items(), 1):
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
    
    servers = config.get("mcpServers", {})
    managed = [(k, v) for k, v in servers.items() if k in MANAGED_SERVERS]
    
    if not managed:
        print_warning("No managed agent servers found in this config.")
        return []
    
    print("The following agent servers are configured:\n")
    
    for i, (key, cfg) in enumerate(managed, 1):
        name = MANAGED_SERVERS.get(key, key)
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {name}")
        print(f"     Key: {key}")
        print(f"     Command: {cfg.get('command', 'N/A')}")
        print()
    
    print(f"  {Colors.BOLD}A.{Colors.ENDC} Remove ALL agent servers")
    print(f"  {Colors.BOLD}Q.{Colors.ENDC} Cancel\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (comma-separated numbers, A for all, Q to cancel): {Colors.ENDC}").strip()
        
        if selection.upper() == 'Q':
            return []
        
        if selection.upper() == 'A':
            return [k for k, v in managed]
        
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(managed):
                    selected.append(managed[idx - 1][0])
                else:
                    raise ValueError(f"Invalid index: {idx}")
            if selected:
                return selected
        except ValueError as e:
            print_error(f"Invalid selection: {e}. Please try again.")


def display_backup_menu(backups: list[Path]) -> Path | None:
    """Display backup selection menu."""
    print_header("Restore from Backup")
    
    if not backups:
        print_warning("No backup files found.")
        return None
    
    print("Available backups:\n")
    
    for i, backup in enumerate(backups[:10], 1):
        print(f"  {Colors.BOLD}{i}.{Colors.ENDC} {backup.name}")
    
    print(f"\n  {Colors.BOLD}Q.{Colors.ENDC} Cancel\n")
    
    while True:
        selection = input(f"{Colors.BOLD}Enter your selection (1-{min(len(backups), 10)}, Q to cancel): {Colors.ENDC}").strip()
        
        if selection.upper() == 'Q':
            return None
        
        try:
            idx = int(selection)
            if 1 <= idx <= min(len(backups), 10):
                return backups[idx - 1]
        except ValueError:
            pass
        
        print_error("Invalid selection. Please try again.")


def restore_from_backup(config_path: Path, backup_path: Path):
    """Restore config from backup file."""
    try:
        import shutil
        shutil.copy2(backup_path, config_path)
        print_success(f"Restored configuration from {backup_path.name}")
    except Exception as e:
        print_error(f"Failed to restore: {e}")


def remove_servers(config_path: Path, servers_to_remove: list[str]):
    """Remove specified servers from config."""
    config = load_config(config_path)
    
    removed = []
    for server in servers_to_remove:
        if server in config.get("mcpServers", {}):
            del config["mcpServers"][server]
            removed.append(server)
    
    save_config(config_path, config)
    
    return removed


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main uninstaller entry point."""
    parser = argparse.ArgumentParser(
        description="Uninstall MCP servers from configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agenters uninstall        # Interactive uninstaller
        """
    )
    parser.parse_args()
    
    print_header("Cooperating Agents MCP Uninstaller")
    
    print("This tool will help you remove MCP servers from your configuration.\n")
    
    # Main menu
    print(f"  {Colors.BOLD}1.{Colors.ENDC} Remove agent servers from config")
    print(f"  {Colors.BOLD}2.{Colors.ENDC} Restore from backup")
    print(f"  {Colors.BOLD}Q.{Colors.ENDC} Quit\n")
    
    selection = input(f"{Colors.BOLD}Enter your selection: {Colors.ENDC}").strip()
    
    if selection.upper() == 'Q':
        print_info("Uninstall cancelled.")
        sys.exit(0)
    
    # Select config file
    config_path = display_config_menu()
    
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    if selection == "2":
        # Restore from backup
        backups = find_backups(config_path)
        backup_path = display_backup_menu(backups)
        if backup_path:
            restore_from_backup(config_path, backup_path)
            print_info("Restart your MCP client for changes to take effect.")
        return
    
    # Remove servers
    config = load_config(config_path)
    servers_to_remove = display_server_removal_menu(config)
    
    if not servers_to_remove:
        print_info("No servers selected for removal.")
        return
    
    # Confirm
    print_header("Confirm Removal")
    print(f"Config file: {config_path}")
    print(f"Servers to remove: {', '.join(servers_to_remove)}\n")
    
    confirm = input(f"{Colors.BOLD}Proceed with removal? [y/N]: {Colors.ENDC}").strip().lower()
    if confirm != 'y':
        print_info("Removal cancelled.")
        return
    
    # Remove
    removed = remove_servers(config_path, servers_to_remove)
    
    if removed:
        print_success(f"Removed {len(removed)} server(s): {', '.join(removed)}")
        print_info("Restart your MCP client for changes to take effect.")
    else:
        print_warning("No servers were removed.")


if __name__ == "__main__":
    main()
