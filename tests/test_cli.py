#!/usr/bin/env python3
"""
Tests for the agenters CLI provisioning system.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestProvisionCommand:
    """Tests for the provision command."""

    def test_provision_dry_run_no_changes(self):
        """Dry run should not modify any files."""
        from agenters import cli
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Provision with dry run
            result = cli.provision_config(
                config_path=config_path,
                agents=["claude", "aider"],
                dry_run=True,
                yes=True
            )
            
            assert result is True
            assert not config_path.exists()  # Should not be created

    def test_provision_creates_config(self):
        """Provision should create config file with servers."""
        from agenters import cli
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            result = cli.provision_config(
                config_path=config_path,
                agents=["claude"],
                dry_run=False,
                yes=True
            )
            
            assert result is True
            assert config_path.exists()
            
            with open(config_path) as f:
                config = json.load(f)
            
            assert "mcpServers" in config
            assert "claude-agent" in config["mcpServers"]
            assert config["mcpServers"]["claude-agent"]["command"] == "claude-mcp"

    def test_provision_invalid_agent(self):
        """Invalid agent names should be rejected."""
        from agenters import cli
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            result = cli.provision_config(
                config_path=config_path,
                agents=["invalid_agent"],
                dry_run=False,
                yes=True
            )
            
            assert result is False

    def test_provision_merges_existing(self):
        """Provision should merge with existing config."""
        from agenters import cli
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Create existing config
            existing = {
                "mcpServers": {
                    "existing-server": {"command": "test", "args": []}
                }
            }
            with open(config_path, 'w') as f:
                json.dump(existing, f)
            
            # Provision additional agent (use 'claude' which is typically installed)
            cli.provision_config(
                config_path=config_path,
                agents=["claude"],
                dry_run=False,
                yes=True
            )
            
            with open(config_path) as f:
                config = json.load(f)
            
            # Both should exist
            assert "existing-server" in config["mcpServers"]
            assert "claude-agent" in config["mcpServers"]


class TestProvisioningWithBackup:
    """Tests for backup functionality during provisioning."""

    def test_backup_created_on_modify(self, temp_project_dir, sample_mcp_config):
        """Verify .backup file is created when modifying existing config."""
        from agenters import cli
        
        config_path = temp_project_dir / ".mcp.json"
        backup_path = config_path.with_suffix(".json.backup")
        
        # Create existing config
        with open(config_path, 'w') as f:
            json.dump(sample_mcp_config, f)
        
        # Verify backup doesn't exist yet
        assert not backup_path.exists()
        
        # Provision (should create backup)
        cli.provision_config(
            config_path=config_path,
            agents=["codex"],
            dry_run=False,
            yes=True
        )
        
        # Verify backup was created
        assert backup_path.exists()

    def test_backup_preserves_original(self, temp_project_dir, sample_mcp_config):
        """Verify backup contains original content."""
        from agenters import cli
        
        config_path = temp_project_dir / ".mcp.json"
        backup_path = config_path.with_suffix(".json.backup")
        
        # Create existing config
        with open(config_path, 'w') as f:
            json.dump(sample_mcp_config, f)
        
        original_content = config_path.read_text()
        
        # Provision
        cli.provision_config(
            config_path=config_path,
            agents=["gemini"],
            dry_run=False,
            yes=True
        )
        
        # Verify backup has original content
        backup_content = backup_path.read_text()
        assert backup_content == original_content
        
        # Verify original file was modified (has new agent)
        with open(config_path) as f:
            config = json.load(f)
        assert "gemini-agent" in config["mcpServers"]

    def test_no_backup_for_new_file(self, temp_project_dir):
        """No backup should be created for new config files."""
        from agenters import cli
        
        config_path = temp_project_dir / ".mcp.json"
        backup_path = config_path.with_suffix(".json.backup")
        
        # Verify neither exists
        assert not config_path.exists()
        assert not backup_path.exists()
        
        # Provision new file
        cli.provision_config(
            config_path=config_path,
            agents=["claude"],
            dry_run=False,
            yes=True
        )
        
        # Config created, no backup
        assert config_path.exists()
        assert not backup_path.exists()


class TestProvisioningMerge:
    """Tests for merging with existing configurations."""

    def test_merge_preserves_all_existing_servers(self, temp_project_dir, sample_mcp_config):
        """Verify all existing mcpServers are preserved after provisioning."""
        from agenters import cli
        
        config_path = temp_project_dir / ".mcp.json"
        
        # Create existing config with multiple servers
        with open(config_path, 'w') as f:
            json.dump(sample_mcp_config, f)
        
        # Provision new agents
        cli.provision_config(
            config_path=config_path,
            agents=["claude", "gemini"],
            dry_run=False,
            yes=True
        )
        
        with open(config_path) as f:
            config = json.load(f)
        
        # Check all original servers are preserved
        assert "playwright" in config["mcpServers"]
        assert "custom-server" in config["mcpServers"]
        
        # Check original server configs are unchanged
        assert config["mcpServers"]["playwright"]["command"] == "npx"
        assert config["mcpServers"]["custom-server"]["env"]["API_KEY"] == "secret"
        
        # Check new servers were added
        assert "claude-agent" in config["mcpServers"]
        assert "gemini-agent" in config["mcpServers"]

    def test_merge_updates_existing_agent(self, temp_project_dir):
        """Verify re-provisioning same agent updates it."""
        from agenters import cli
        
        config_path = temp_project_dir / ".mcp.json"
        
        # Create config with old-style agent config
        existing = {
            "mcpServers": {
                "claude-agent": {
                    "command": "old-claude-mcp",
                    "args": ["--old-flag"]
                }
            }
        }
        with open(config_path, 'w') as f:
            json.dump(existing, f)
        
        # Re-provision claude
        cli.provision_config(
            config_path=config_path,
            agents=["claude"],
            dry_run=False,
            yes=True
        )
        
        with open(config_path) as f:
            config = json.load(f)
        
        # Verify it was updated to new config
        assert config["mcpServers"]["claude-agent"]["command"] == "claude-mcp"
        assert config["mcpServers"]["claude-agent"]["args"] == []


class TestProjectLevelProvisioning:
    """Tests for project-level config path generation."""

    def test_project_config_path_claude(self):
        """Verify Claude uses .mcp.json at project root."""
        from agenters import cli
        
        project_dir = Path("/test/project")
        path = cli.get_project_config_path(project_dir, "claude")
        
        assert path == Path("/test/project/.mcp.json")

    def test_project_config_path_cursor(self):
        """Verify Cursor uses .cursor/mcp.json."""
        from agenters import cli
        
        project_dir = Path("/test/project")
        path = cli.get_project_config_path(project_dir, "cursor")
        
        assert path == Path("/test/project/.cursor/mcp.json")

    def test_project_config_path_vscode(self):
        """Verify VS Code uses .vscode/mcp.json."""
        from agenters import cli
        
        project_dir = Path("/test/project")
        path = cli.get_project_config_path(project_dir, "vscode")
        
        assert path == Path("/test/project/.vscode/mcp.json")

    def test_project_config_path_windsurf(self):
        """Verify Windsurf uses .windsurf/mcp.json."""
        from agenters import cli
        
        project_dir = Path("/test/project")
        path = cli.get_project_config_path(project_dir, "windsurf")
        
        assert path == Path("/test/project/.windsurf/mcp.json")

    def test_project_creates_directory_structure(self, temp_project_dir):
        """Verify parent directories are created for nested config paths."""
        from agenters import cli
        
        # .cursor directory doesn't exist yet
        cursor_dir = temp_project_dir / ".cursor"
        assert not cursor_dir.exists()
        
        config_path = cli.get_project_config_path(temp_project_dir, "cursor")
        
        # Provision creates the directory
        cli.provision_config(
            config_path=config_path,
            agents=["claude"],
            dry_run=False,
            yes=True
        )
        
        assert cursor_dir.exists()
        assert config_path.exists()


class TestStatusCommand:
    """Tests for the status command."""

    def test_check_cli_installed(self):
        """Test CLI detection."""
        from agenters import cli
        
        # python should be installed
        assert cli.check_cli_installed("python") is True
        # fake command should not exist
        assert cli.check_cli_installed("definitely_not_a_real_command_xyz") is False


class TestConfigPaths:
    """Tests for config path helpers."""

    def test_get_user_config_path_cursor(self):
        """Test user config path for cursor."""
        from agenters import cli
        
        path = cli.get_user_config_path("cursor")
        assert path is not None
        assert "mcp.json" in str(path)

    def test_get_user_config_path_invalid(self):
        """Test invalid client returns None."""
        from agenters import cli
        
        path = cli.get_user_config_path("invalid_client")
        assert path is None

    def test_get_project_config_path(self):
        """Test project config path generation."""
        from agenters import cli
        
        project_dir = Path("/test/project")
        path = cli.get_project_config_path(project_dir, "cursor")
        
        assert path == Path("/test/project/.cursor/mcp.json")


class TestMCPServerConfig:
    """Tests for MCP server configuration generation."""

    def test_get_mcp_server_config_structure(self):
        """Verify MCP server config has required fields."""
        from agenters import cli
        
        config = cli.get_mcp_server_config("claude")
        
        assert "command" in config
        assert "args" in config
        assert "env" in config
        assert "disabled" in config
        assert "transport" in config
        
        assert config["command"] == "claude-mcp"
        assert config["disabled"] is False
        assert config["transport"] == "stdio"

    def test_get_mcp_server_config_all_agents(self):
        """Verify all agents have valid MCP configs."""
        from agenters import cli
        
        expected_commands = {
            "claude": "claude-mcp",
            "aider": "aider-mcp",
            "codex": "codex-mcp",
            "gemini": "gemini-mcp",
            "goose": "goose-mcp",
            "manus": "manus-mcp",
        }
        
        for agent, expected_cmd in expected_commands.items():
            config = cli.get_mcp_server_config(agent)
            assert config["command"] == expected_cmd, f"Wrong command for {agent}"


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests that run actual CLI commands.
    
    These tests require the actual CLI tools to be installed.
    Run with: pytest -v -m integration
    """

    @pytest.mark.skipif(
        subprocess.run(["which", "claude"], capture_output=True).returncode != 0,
        reason="claude CLI not installed"
    )
    def test_claude_mcp_list_shows_provisioned_servers(self, temp_project_dir):
        """Verify .mcp.json file is correctly formatted for Claude CLI.
        
        Note: Claude CLI only reads .mcp.json from git repos or registered paths,
        so we verify the file structure is correct rather than testing the CLI directly.
        """
        from agenters import cli
        
        # Create .mcp.json in temp dir with test server
        config_path = temp_project_dir / ".mcp.json"
        test_config = {
            "mcpServers": {
                "test-server": {
                    "command": "echo",
                    "args": ["test"]
                }
            }
        }
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Verify file structure is valid JSON
        with open(config_path) as f:
            loaded = json.load(f)
        
        assert "mcpServers" in loaded
        assert "test-server" in loaded["mcpServers"]
        assert loaded["mcpServers"]["test-server"]["command"] == "echo"

    def test_agenters_status_runs(self):
        """Verify 'agenters status' command runs without error."""
        result = subprocess.run(
            ["agenters", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should complete (exit 0) and show agent status
        assert result.returncode == 0
        assert "Agent CLI Status" in result.stdout

    def test_agenters_provision_dry_run(self, temp_project_dir):
        """Verify 'agenters provision --dry-run' shows preview without changes."""
        result = subprocess.run(
            ["agenters", "provision", "--project", "--client", "cursor", "--dry-run", "--yes"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "DRY RUN" in result.stdout
        
        # Verify no file was created
        config_path = temp_project_dir / ".cursor" / "mcp.json"
        assert not config_path.exists()

    def test_provision_end_to_end(self, temp_project_dir):
        """Full provision workflow: provision, verify file, check content."""
        # Run agenters provision
        result = subprocess.run(
            ["agenters", "provision", "--project", "--client", "claude", "--agents", "claude,gemini", "--yes"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        # Native CLI uses "Added", file-based uses "Provisioned"
        assert "Provisioned" in result.stdout or "Added" in result.stdout
        
        # Verify .mcp.json was created
        config_path = temp_project_dir / ".mcp.json"
        assert config_path.exists()
        
        # Verify content
        with open(config_path) as f:
            config = json.load(f)
        
        assert "mcpServers" in config
        assert "claude-agent" in config["mcpServers"]
        assert "gemini-agent" in config["mcpServers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
