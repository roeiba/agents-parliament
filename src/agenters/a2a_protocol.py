"""
A2A Protocol Module

Implements a simplified version of Google's Agent2Agent (A2A) protocol
for agent capability discovery and task delegation in the Agents Parliament.

This module provides:
- AgentCard: Capability descriptors for agents
- A2ADiscovery: Agent discovery and routing
- A2ACoordinator: Multi-agent task coordination
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("a2a-protocol")


@dataclass
class AgentCard:
    """
    Agent capability card for A2A protocol discovery.
    
    Based on Google's A2A protocol agent card specification.
    """
    name: str
    version: str
    publisher: str
    description: str
    strengths: list[str]
    context_window: str
    tools: list[str]
    supported_features: dict = field(default_factory=dict)
    
    def matches_requirement(self, requirement: str) -> bool:
        """Check if agent matches a given requirement."""
        req_lower = requirement.lower()
        
        # Check strengths
        for strength in self.strengths:
            if req_lower in strength.lower():
                return True
        
        # Check description
        if req_lower in self.description.lower():
            return True
        
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "publisher": self.publisher,
            "description": self.description,
            "strengths": self.strengths,
            "context_window": self.context_window,
            "tools": self.tools,
            "supported_features": self.supported_features,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentCard":
        """Create AgentCard from dictionary."""
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            publisher=data.get("publisher", "Unknown"),
            description=data.get("description", ""),
            strengths=data.get("strengths", []),
            context_window=data.get("context_window", "unknown"),
            tools=data.get("tools", []),
            supported_features=data.get("supported_features", {}),
        )


class A2ADiscovery:
    """
    Agent discovery service for A2A protocol.
    
    Loads and manages agent capability cards for routing decisions.
    """
    
    def __init__(self, cards_file: Optional[str] = None):
        """
        Initialize discovery service.
        
        Args:
            cards_file: Path to agent_cards.json file. If None, uses default location.
        """
        self.agents: dict[str, AgentCard] = {}
        
        # Default cards file location
        if cards_file is None:
            cards_file = Path(__file__).parent / "agent_cards.json"
        
        self._load_cards(Path(cards_file))
    
    def _load_cards(self, cards_file: Path) -> None:
        """Load agent cards from JSON file."""
        if not cards_file.exists():
            logger.warning(f"Agent cards file not found: {cards_file}")
            return
        
        try:
            with open(cards_file, "r") as f:
                data = json.load(f)
            
            for agent_data in data.get("agents", []):
                card = AgentCard.from_dict(agent_data)
                self.agents[card.name] = card
                logger.info(f"Loaded agent card: {card.name}")
            
        except Exception as e:
            logger.error(f"Error loading agent cards: {e}")
    
    def discover_all(self) -> list[AgentCard]:
        """Return all registered agent cards."""
        return list(self.agents.values())
    
    def get_agent(self, name: str) -> Optional[AgentCard]:
        """Get a specific agent card by name."""
        return self.agents.get(name)
    
    def find_by_strength(self, strength: str) -> list[AgentCard]:
        """Find agents with a specific strength."""
        matching = []
        strength_lower = strength.lower()
        
        for card in self.agents.values():
            for s in card.strengths:
                if strength_lower in s.lower():
                    matching.append(card)
                    break
        
        return matching
    
    def find_best_for_task(self, task_description: str) -> Optional[AgentCard]:
        """
        Find the best agent for a given task based on capability matching.
        
        Args:
            task_description: Description of the task to perform
        
        Returns:
            Best matching AgentCard, or None if no match found
        """
        # Define keyword to strength mappings
        task_mappings = {
            "search": "search-grounding",
            "web": "search-grounding",
            "real-time": "real-time-data",
            "current": "real-time-data",
            "large": "large-context",
            "analyze": "large-context",
            "code": "coding",
            "program": "coding",
            "debug": "coding",
            "git": "git-integration",
            "commit": "git-integration",
            "diff": "diff-handling",
            "autonomous": "autonomous-operation",
            "workflow": "multi-step-workflows",
            "recipe": "recipe-based-automation",
            "sandbox": "sandboxed-execution",
            "reason": "deep-reasoning",
            "plan": "multi-step-planning",
            "json": "structured-output",
        }
        
        task_lower = task_description.lower()
        scores: dict[str, int] = {}
        
        for keyword, strength in task_mappings.items():
            if keyword in task_lower:
                matching = self.find_by_strength(strength)
                for card in matching:
                    scores[card.name] = scores.get(card.name, 0) + 1
        
        if not scores:
            # Default to Claude for general tasks
            return self.get_agent("claude-agent")
        
        # Return agent with highest score
        best_name = max(scores, key=lambda x: scores[x])
        return self.get_agent(best_name)


class A2ACoordinator:
    """
    Coordinator for multi-agent task execution.
    
    Routes tasks to appropriate agents and manages collaboration.
    """
    
    def __init__(self, discovery: Optional[A2ADiscovery] = None):
        """
        Initialize coordinator.
        
        Args:
            discovery: A2ADiscovery service. Creates new one if None.
        """
        self.discovery = discovery or A2ADiscovery()
    
    def route_task(self, task: str) -> tuple[Optional[AgentCard], str]:
        """
        Route a task to the best agent.
        
        Args:
            task: Task description
        
        Returns:
            Tuple of (AgentCard, reasoning)
        """
        agent = self.discovery.find_best_for_task(task)
        
        if agent is None:
            return None, "No suitable agent found for this task"
        
        # Build reasoning
        matched_strengths = [s for s in agent.strengths if any(
            kw in task.lower() for kw in s.split("-")
        )]
        
        if matched_strengths:
            reasoning = f"Selected {agent.name} for strengths: {', '.join(matched_strengths)}"
        else:
            reasoning = f"Selected {agent.name} as default for general capability"
        
        return agent, reasoning
    
    def get_agent_for_strength(self, strength: str) -> Optional[AgentCard]:
        """Get the best agent for a specific strength requirement."""
        agents = self.discovery.find_by_strength(strength)
        return agents[0] if agents else None
    
    def suggest_collaboration(self, complex_task: str) -> list[tuple[AgentCard, str]]:
        """
        Suggest a collaboration of agents for a complex task.
        
        Args:
            complex_task: Description of a complex multi-step task
        
        Returns:
            List of (AgentCard, suggested_subtask) tuples
        """
        suggestions = []
        task_lower = complex_task.lower()
        
        # Check for web research needs
        if any(kw in task_lower for kw in ["search", "web", "current", "latest"]):
            agent = self.discovery.get_agent("gemini-agent")
            if agent:
                suggestions.append((agent, "Research and gather current information"))
        
        # Check for code changes
        if any(kw in task_lower for kw in ["code", "implement", "fix", "refactor"]):
            agent = self.discovery.get_agent("claude-agent")
            if agent:
                suggestions.append((agent, "Implement code changes with reasoning"))
        
        # Check for git operations
        if any(kw in task_lower for kw in ["git", "commit", "branch", "merge"]):
            agent = self.discovery.get_agent("aider-agent")
            if agent:
                suggestions.append((agent, "Handle Git operations and code edits"))
        
        # Check for autonomous workflows
        if any(kw in task_lower for kw in ["automate", "workflow", "pipeline"]):
            agent = self.discovery.get_agent("goose-agent")
            if agent:
                suggestions.append((agent, "Execute autonomous workflow"))
        
        # Check for sandboxed execution
        if any(kw in task_lower for kw in ["sandbox", "safe", "test"]):
            agent = self.discovery.get_agent("codex-agent")
            if agent:
                suggestions.append((agent, "Run in sandboxed environment"))
        
        return suggestions


# Convenience functions for quick access
def discover_agents(cards_file: Optional[str] = None) -> list[AgentCard]:
    """Discover all available agents."""
    discovery = A2ADiscovery(cards_file)
    return discovery.discover_all()


def find_best_agent(task: str, cards_file: Optional[str] = None) -> Optional[AgentCard]:
    """Find the best agent for a task."""
    discovery = A2ADiscovery(cards_file)
    return discovery.find_best_for_task(task)


def route_task(task: str, cards_file: Optional[str] = None) -> tuple[Optional[AgentCard], str]:
    """Route a task to the best agent with reasoning."""
    coordinator = A2ACoordinator(A2ADiscovery(cards_file))
    return coordinator.route_task(task)
