---
name: blucli
description: |
  Control Bluesound/NAD players using the blu CLI tool.
  Use when: managing playback, volume, grouping, or TuneIn on Bluesound/NAD
  devices; scripting player control; or selecting target devices by ID, name, or alias.
---

# blucli (blu)

Use `blu` to control Bluesound/NAD players.

## Quick Start

```bash
blu devices          # list available devices, pick target
blu --device <id> status
blu play|pause|stop
blu volume set 15
```

## Target Selection (priority order)

1. `--device <id|name|alias>`
2. `BLU_DEVICE` environment variable
3. Config default (if set)

## Common Tasks

```bash
# Grouping
blu group status
blu group add
blu group remove

# TuneIn
blu tunein search "query"
blu tunein play "query"
```

## Tips

- Use `--json` for scripting
- Confirm the target device before changing playback
