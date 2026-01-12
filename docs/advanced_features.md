# Advanced Features

This document covers the advanced features available in Agents Parliament v2.0.

## A2A Protocol Support

The Agent-to-Agent (A2A) protocol enables capability discovery and intelligent task routing.

### Agent Cards

Each agent has a capability card that describes its strengths and tools:

```python
from agenters.a2a_protocol import discover_agents

for agent in discover_agents():
    print(f"{agent.name}: {agent.description}")
    print(f"  Strengths: {', '.join(agent.strengths)}")
```

### Task Routing

Automatically route tasks to the best agent:

```python
from agenters.a2a_protocol import find_best_agent

# Web research → Gemini (search-grounding)
agent = find_best_agent("Find latest Python 3.13 features")

# Code changes with Git → Aider (git-integration)
agent = find_best_agent("Refactor auth module and commit")

# Complex reasoning → Claude (deep-reasoning)
agent = find_best_agent("Design a microservices architecture")
```

---

## Claude Features

### Hooks

Execute shell commands before/after Claude processes prompts:

```python
# Pre-hook: Run linter before Claude sees the code
# Post-hook: Run tests after Claude makes changes
ask_claude_with_hooks(
    prompt="Fix the bug in utils.py",
    pre_hook="ruff check .",
    post_hook="pytest tests/"
)
```

### Skills

Load specialized skills for domain-specific tasks:

```markdown
# Create: skills/code_review/SKILL.md
You are a code reviewer focused on security...
```

```python
ask_claude_with_skill(
    prompt="Review auth.py",
    skill_name="code_review"
)
```

### Sub-Agent Spawning

Dynamically create specialized agents:

```python
spawn_claude_agent(
    task_description="Analyze security vulnerabilities",
    agent_instructions="Focus on OWASP Top 10...",
    allowed_tools="Read,Bash"
)
```

---

## Gemini Features

### Playbooks

Pre-configured guides for specific tasks:

```markdown
# Create: playbooks/research.md
When researching, use Google Search grounding...
```

```python
gemini_with_playbook(
    prompt="Research AI agent protocols",
    playbook_name="research"
)
```

---

## Goose Features

### Toolkits

Enable MCP extensions for integrations:

```python
goose_with_toolkits(
    instructions="Create GitHub issue for bug",
    toolkits="github,jira"
)
```

### Recipes

YAML-defined reusable workflows:

```yaml
# recipes/full_tdd.yaml
steps:
  - Write tests
  - Implement feature
  - Refactor
  - Document
```

---

## Mesh Coordination

### Multi-Agent Collaboration

```python
from agenters.mesh_coordinator import create_mesh

mesh = create_mesh()

# Get team suggestions
team = mesh.suggest_team(
    "Research APIs, implement integration, test, deploy"
)
# [(gemini, "Research"), (claude, "Implement"), 
#  (aider, "Test"), (goose, "Deploy")]
```

### Workflow Engine

```python
from agenters.mesh_coordinator import create_workflow

workflow = (
    create_workflow()
    .add_step("research", "Find APIs", "Search for REST APIs")
    .add_step("implement", "Code it", "Implement the client", 
              depends_on=["research"])
)

print(workflow.get_execution_order())
# [["research"], ["implement"]]
```

---

## Resources

Pre-packaged skills, recipes, and playbooks are available in:

```
src/agenters/resources/
├── skills/         # Claude SKILL.md files
├── recipes/        # Goose YAML recipes
├── playbooks/      # Gemini playbooks
└── hooks/          # Shell hook scripts
```
