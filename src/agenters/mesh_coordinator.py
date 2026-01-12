"""
Mesh Coordinator Module

Provides full mesh agent coordination for the Agents Parliament.
Enables any agent to call any other agent, creating a collaborative
network of specialized AI assistants.

This module provides:
- AgentMesh: Registry and routing for the agent network
- WorkflowEngine: Multi-step workflow execution across agents
- Convenience functions for quick agent coordination
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from .a2a_protocol import A2ADiscovery, AgentCard, A2ACoordinator

logger = logging.getLogger("mesh-coordinator")


class TaskStatus(Enum):
    """Status of a task in the workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    agent_name: str
    status: TaskStatus
    output: str
    error: Optional[str] = None
    duration_ms: int = 0
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    step_id: str
    description: str
    agent_name: Optional[str] = None  # If None, auto-route
    prompt: str = ""
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None


class AgentMesh:
    """
    Full mesh network of cooperating agents.
    
    Enables any agent to discover and invoke any other agent,
    creating a collaborative network for complex tasks.
    """
    
    def __init__(self, cards_file: Optional[str] = None):
        """
        Initialize the agent mesh.
        
        Args:
            cards_file: Path to agent_cards.json. Uses default if None.
        """
        self.discovery = A2ADiscovery(cards_file)
        self.coordinator = A2ACoordinator(self.discovery)
        self._tool_registry: dict[str, Callable] = {}
        
        logger.info(f"Agent mesh initialized with {len(self.discovery.agents)} agents")
    
    @property
    def agents(self) -> dict[str, AgentCard]:
        """Get all registered agents."""
        return self.discovery.agents
    
    def register_tool(self, agent_name: str, tool_name: str, handler: Callable) -> None:
        """
        Register a tool handler for an agent.
        
        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            handler: Async callable that executes the tool
        """
        key = f"{agent_name}:{tool_name}"
        self._tool_registry[key] = handler
        logger.debug(f"Registered tool: {key}")
    
    def route_to_best_agent(self, task: str) -> tuple[Optional[AgentCard], str]:
        """
        Route a task to the best agent based on capabilities.
        
        Args:
            task: Task description
        
        Returns:
            Tuple of (AgentCard, reasoning)
        """
        return self.coordinator.route_task(task)
    
    def find_agents_for_capability(self, capability: str) -> list[AgentCard]:
        """
        Find all agents with a specific capability/strength.
        
        Args:
            capability: The capability to search for
        
        Returns:
            List of matching agents
        """
        return self.discovery.find_by_strength(capability)
    
    def get_agent(self, name: str) -> Optional[AgentCard]:
        """Get a specific agent by name."""
        return self.discovery.get_agent(name)
    
    def suggest_team(self, complex_task: str) -> list[tuple[AgentCard, str]]:
        """
        Suggest a team of agents for a complex task.
        
        Args:
            complex_task: Description of a complex multi-part task
        
        Returns:
            List of (AgentCard, suggested_subtask) tuples
        """
        return self.coordinator.suggest_collaboration(complex_task)
    
    def get_mesh_status(self) -> dict:
        """Get current status of the agent mesh."""
        return {
            "active_agents": len(self.agents),
            "agents": [card.name for card in self.agents.values()],
            "registered_tools": len(self._tool_registry),
        }


class WorkflowEngine:
    """
    Execute multi-step workflows across agents.
    
    Supports:
    - Sequential execution
    - Parallel execution
    - Dependency-based execution order
    - Result passing between steps
    """
    
    def __init__(self, mesh: Optional[AgentMesh] = None):
        """
        Initialize workflow engine.
        
        Args:
            mesh: AgentMesh instance. Creates new one if None.
        """
        self.mesh = mesh or AgentMesh()
        self.steps: list[WorkflowStep] = []
        self.results: dict[str, TaskResult] = {}
    
    def add_step(
        self,
        step_id: str,
        description: str,
        prompt: str,
        agent_name: Optional[str] = None,
        depends_on: Optional[list[str]] = None,
    ) -> "WorkflowEngine":
        """
        Add a step to the workflow.
        
        Args:
            step_id: Unique identifier for this step
            description: Human-readable description
            prompt: The prompt to send to the agent
            agent_name: Specific agent to use. Auto-routes if None.
            depends_on: List of step_ids this step depends on
        
        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            step_id=step_id,
            description=description,
            agent_name=agent_name,
            prompt=prompt,
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        return self
    
    def get_execution_order(self) -> list[list[str]]:
        """
        Determine execution order based on dependencies.
        
        Returns:
            List of step batches that can run in parallel
        """
        completed: set[str] = set()
        remaining = {s.step_id: s for s in self.steps}
        batches: list[list[str]] = []
        
        while remaining:
            # Find steps with all dependencies satisfied
            ready = []
            for step_id, step in remaining.items():
                if all(dep in completed for dep in step.depends_on):
                    ready.append(step_id)
            
            if not ready:
                # Circular dependency or missing dependency
                logger.warning(f"Cannot resolve dependencies for: {list(remaining.keys())}")
                break
            
            batches.append(ready)
            completed.update(ready)
            for step_id in ready:
                del remaining[step_id]
        
        return batches
    
    def to_dict(self) -> dict:
        """Serialize workflow to dictionary."""
        return {
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "agent_name": s.agent_name,
                    "prompt": s.prompt,
                    "depends_on": s.depends_on,
                    "status": s.status.value,
                }
                for s in self.steps
            ],
            "execution_order": self.get_execution_order(),
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }
    
    @classmethod
    def from_yaml(cls, yaml_content: str, mesh: Optional[AgentMesh] = None) -> "WorkflowEngine":
        """
        Create workflow from YAML content.
        
        Expected format:
        ```yaml
        steps:
          - id: step1
            description: First step
            prompt: Do something
            agent: claude-agent  # optional
          - id: step2
            description: Second step
            prompt: Do something else
            depends_on:
              - step1
        ```
        """
        try:
            import yaml
            data = yaml.safe_load(yaml_content)
        except ImportError:
            # Fall back to JSON-style YAML
            import json
            data = json.loads(yaml_content)
        
        engine = cls(mesh)
        
        for step_data in data.get("steps", []):
            engine.add_step(
                step_id=step_data["id"],
                description=step_data.get("description", ""),
                prompt=step_data.get("prompt", ""),
                agent_name=step_data.get("agent"),
                depends_on=step_data.get("depends_on", []),
            )
        
        return engine


# Convenience functions
def create_mesh(cards_file: Optional[str] = None) -> AgentMesh:
    """Create a new agent mesh."""
    return AgentMesh(cards_file)


def route_task(task: str) -> tuple[Optional[AgentCard], str]:
    """Route a task to the best agent."""
    mesh = AgentMesh()
    return mesh.route_to_best_agent(task)


def create_workflow() -> WorkflowEngine:
    """Create a new workflow engine."""
    return WorkflowEngine()


def get_all_agents() -> list[AgentCard]:
    """Get all available agents."""
    mesh = AgentMesh()
    return list(mesh.agents.values())


def get_agent_tools(agent_name: str) -> list[str]:
    """Get all tools for a specific agent."""
    mesh = AgentMesh()
    agent = mesh.get_agent(agent_name)
    return agent.tools if agent else []
