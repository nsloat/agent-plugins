# agent-plugins

Nathan Sloat's Claude Code plugin marketplace.

## Install

```
/plugin marketplace add nsloat/agent-plugins
/plugin install <plugin-name>@agent-plugins
```

## Plugins

| Plugin | Description |
| --- | --- |
| [hello-world](plugins/hello-world) | Example plugin demonstrating marketplace registration. |
| [project](plugins/project) | Manage multi-repo "projects" — a named effort with one git worktree per repo, all sharing a branch, from setup through finish. |

## Adding a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with `name`, `displayName`, `description`, `version`.
2. Add the skill(s) under `plugins/<name>/skills/<skill>/SKILL.md`.
3. Register the plugin in `.claude-plugin/marketplace.json`.

See `plugins/hello-world` for the minimal shape, or `plugins/project` for a
plugin that bundles a helper script and tests.
