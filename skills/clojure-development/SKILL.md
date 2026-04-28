---
name: clojure-development
description: |
  Clojure development workflow for Metabase codebases with REPL-driven development.
  Use when: writing or editing Clojure code, working with the REPL, using clojure-mcp
  tools, following functional programming principles, or evaluating namespaces
  and composing functions bottom-up.
---

# Clojure Development Skill

## Tool Preference

When `clojure-mcp` tools are available (e.g., `clojure_eval`, `clojure_edit`), **always use them**
instead of shell commands like `./bin/mage -repl`. The MCP tools provide:
- Direct REPL integration without shell escaping issues
- Better error messages and feedback
- Structural Clojure editing that prevents syntax errors

Only fall back to `./bin/mage` commands when clojure-mcp is not available.

@./../_shared/development-workflow.md
@./../_shared/clojure-style-guide.md
@./../_shared/clojure-commands.md

## REPL-Driven Development Workflow

- **Start with small, fundamental functions**: Identify the core features required for your task and break each down into the smallest, most basic functions that can be developed and tested independently.
- **Write and test in the REPL**: Write code for each small function directly in the REPL. Test thoroughly with a variety of inputs, including typical use cases and relevant edge cases.
- **Integrate into source code**: Once a function works correctly in the REPL, move it into your source code files within appropriate namespaces.
- **Gradually increase complexity**: Build upon tested, basic functions to create more complex functions or components. Compose smaller functions together, testing each new composition in the REPL step by step.
- **Ensure dependency testing**: Make sure every function is fully tested in the REPL before it is depended upon by other functions.
- **Use the REPL fully**: Use the REPL as your primary tool to experiment with different approaches, iterate quickly, and get immediate feedback.
- **Follow functional programming principles**: Keep functions small, focused, and composable. Use Clojure's functional programming features — immutability, higher-order functions, and the standard library — to write concise, effective code.

## How to Evaluate Code

### Bottom-up Dev Loop

1. Write code into a file.
2. Evaluate the file's namespace and make sure it loads correctly:
   ```bash
   ./bin/mage -repl --namespace metabase.app-db.connection
   ```
3. Call functions in the namespace with test inputs and observe that outputs are correct. Feel free to copy these REPL session trials into actual test cases using `deftest` and `is`.
4. Once you know these functions are good, return to step 1 and compose them into the task you need to build.

## Critical Rules for Editing

- Be careful with parentheses counts when editing Clojure code
- After EVERY change to Clojure code, verify readability with `-check-readable`
- End all files with a newline
- When editing tabular code where columns line up, keep them aligned
- Spaces on a line with nothing after it are not allowed
