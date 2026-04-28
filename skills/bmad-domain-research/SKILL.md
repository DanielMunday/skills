---
name: bmad-domain-research
description: 'Conduct domain and industry research. Use when the user says wants to do domain research for a topic or industry'
---

# Domain Research Workflow

## Overview

This workflow enables comprehensive domain and industry research by combining web search capabilities with expert research methodology. You'll facilitate research collaborations that produce complete, well-sourced research documents.

## Conventions

Bare paths (e.g. `domain-steps/step-01-init.md`) resolve from the skill root. `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).

## PREREQUISITE

⛔ Web search required. If unavailable, abort and tell the user.

## On Activation

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

**If the script fails**, resolve the `workflow` block yourself by reading these three files in base → team → user order and merging according to BMad structural rules:
- `{skill-root}/customize.toml`
- `{project-root}/_bmad/bmm/team-customizations.toml` (if it exists)
- `{project-root}/_bmad/bmm/user-customizations.toml` (if it exists)

Merge rules:
- **scalars**: override wins
- **arrays** (`persistent_facts`, `activation_steps_*`): append
- **arrays-of-tables** with `code`/`id`: replace matching items, append new ones

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context you carry for the rest of the workflow run.

### Step 4: Load Config

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:
- Use `{user_name}` for greeting
- Use `{communication_language}` for all communications
- Use `{planning_artifacts}` for output file paths

### Step 5: Greet the User

Greet `{user_name}`, speaking in `{communication_language}`.

### Step 6: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

## QUICK TOPIC DISCOVERY

Welcome `{user_name}`! Let's get started with your **domain/industry research**.

**What domain, industry, or sector do you want to research?**

### Topic Clarification

Based on the user's topic, briefly clarify:

1. **Core Domain**: "What specific aspect of [domain] are you most interested in?"
2. **Research Goals**: "What outcomes are you hoping to achieve with this research?"
3. **Scope**: "Are you looking for a broad overview or a deep dive into specific areas?"

## ROUTE TO DOMAIN RESEARCH STEPS

After gathering the topic and goals:

1. Set `research_type = "domain"`
2. Set `research_topic = [discovered topic from discussion]`
3. Set `research_goals = [captured goals from discussion]`
4. Create starter research document at:
   `{planning_artifacts}/research/domain-{research_topic_slug}-research-{date}.md`
   using `research.template.md` as the template, substituting all `{{placeholder}}` values
5. Load `./domain-steps/step-01-init.md` to begin the domain research pipeline
