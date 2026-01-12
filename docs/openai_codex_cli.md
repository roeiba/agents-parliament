# OpenAI Codex CLI

**Publisher:** OpenAI

## Overview
Codex CLI is optimized for small, focused code tasks. It excels at quick, pinpointed edits rather than large architectural changes.

## Primary Use Cases (When to Delegate to Codex)
- **Small Code Edits**: Quick bug fixes, adding a function, simple refactors
- **Natural Language to Code**: Converting English instructions into shell commands or snippets
- **Sandboxed Execution**: Safe "full-auto" mode for autonomous changes in isolation
- **One-shot Tasks**: Tasks that can be completed in a single focused action

## When NOT to Use Codex
- Large-scale refactoring (prefer Claude or Aider)
- Tasks requiring deep reasoning or multi-step planning (prefer Claude)
- Git-integrated workflows (prefer Aider)
- Web browsing or research (prefer Gemini)

## Key Features
- **Approval Modes:** Three levels of autonomy:
  - `suggest` - Shows proposed changes, requires approval
  - `auto-edit` - Auto-applies file edits, asks for shell commands
  - `full-auto` - Fully autonomous in sandboxed environment
- **Sandboxed Execution:** Network-disabled, directory-scoped safety
- **Fast Turnaround:** Optimized for quick, focused responses
- **Multimodal Support:** Can accept screenshots to guide code generation
