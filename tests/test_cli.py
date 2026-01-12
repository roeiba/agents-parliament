#!/usr/bin/env python3
"""
Tests for the agenters CLI provisioning system.
"""

import json
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
            
            # Provision additional agent
            cli.provision_config(
                config_path=config_path,
                agents=["aider"],
                dry_run=False,
                yes=True
            )
            
            with open(config_path) as f:
                config = json.load(f)
            
            # Both should exist
            assert "existing-server" in config["mcpServers"]
            assert "aider-agent" in config["mcpServers"]


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
