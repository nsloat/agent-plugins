# agent-plugins

A Claude Code plugin marketplace. `.claude-plugin/marketplace.json` lists the
plugins; each plugin lives under `plugins/<name>/`.

## Structure

- `plugins/<name>/.claude-plugin/plugin.json` — plugin manifest (`name`,
  `displayName`, `description`, `version`).
- `plugins/<name>/skills/<skill>/SKILL.md` — one or more skills per plugin,
  with YAML frontmatter (`name`, `description`, `user-invocable`,
  `allowed-tools`). The `description` is what triggers the skill, so it must
  state the triggering phrases/situations explicitly.
- A plugin can bundle a helper script alongside its `SKILL.md` (see
  `plugins/project/skills/project/project_tool.py`) for deterministic logic
  the skill shouldn't reimplement in prose. Resolve it via
  `${CLAUDE_PLUGIN_ROOT}`.

## Adding a plugin

1. Scaffold `plugins/<name>/.claude-plugin/plugin.json` and
   `plugins/<name>/skills/<skill>/SKILL.md`.
2. Register the plugin in `.claude-plugin/marketplace.json` (`name`,
   `source`, `description`).
3. If the skill needs deterministic mechanics (not just instructions), add a
   helper script with tests next to it — see `plugins/project/skills/project/`.

## Tests

Plugins with helper scripts have pytest tests alongside them, e.g.:

```
cd plugins/project/skills/project && python3 -m pytest
```

## Conventions

- Branches/PRs use `type/short-description` naming (`feat/...`, `fix/...`).
- PRs are merged via GitHub (see closed PRs for examples); no direct pushes
  to `main` outside of small fixes.
