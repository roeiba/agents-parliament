#!/usr/bin/env python3
"""
Pytest fixtures for agenters CLI tests.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory with realistic structure.
    
    Yields the temp directory path and cleans up after.
    """
    tmpdir = tempfile.mkdtemp(prefix="agenters_test_")
    project_dir = Path(tmpdir)
    
    # Create some typical project files
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").touch()
    (project_dir / "README.md").write_text("# Test Project\n")
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    
    yield project_dir
    
    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_home_dir(monkeypatch) -> Generator[Path, None, None]:
    """Create a temporary home directory for testing global configs.
    
    Patches Path.home() to return the temp directory.
    """
    tmpdir = tempfile.mkdtemp(prefix="agenters_home_")
    home_dir = Path(tmpdir)
    
    # Create expected directories for various clients
    (home_dir / ".cursor").mkdir()
    (home_dir / ".codeium" / "windsurf").mkdir(parents=True)
    (home_dir / ".gemini" / "antigravity").mkdir(parents=True)
    (home_dir / "Library" / "Application Support" / "Claude").mkdir(parents=True)
    (home_dir / "Library" / "Application Support" / "Code" / "User" / "globalStorage").mkdir(parents=True)
    
    # Patch Path.home
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    
    yield home_dir
    
    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_mcp_config() -> dict:
    """Return a sample MCP config with existing servers."""
    return {
        "mcpServers": {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"]
            },
            "custom-server": {
                "command": "my-custom-mcp",
                "args": ["--port", "8080"],
                "env": {"API_KEY": "secret"}
            }
        }
    }


@pytest.fixture
def sample_mcp_config_file(temp_project_dir, sample_mcp_config) -> Path:
    """Create a sample .mcp.json file in the temp project directory."""
    config_path = temp_project_dir / ".mcp.json"
    with open(config_path, 'w') as f:
        json.dump(sample_mcp_config, f, indent=2)
    return config_path
