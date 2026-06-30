# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code plugin marketplace (Nathan Sloat's). `.claude-plugin/marketplace.json`
is the marketplace manifest — it lists every plugin and where to find it.
Installing this marketplace and a plugin from it works via:

```
/plugin marketplace add nsloat/agent-plugins
/plugin install <plugin-name>@agent-plugins
```

## Adding a new plugin

Each plugin is a standalone directory under `plugins/<name>/`. Creating one
is a separate step from registering it:

1. Create `plugins/<name>/.claude-plugin/plugin.json`. `name` is the only
   required field (kebab-case — it becomes the skill namespace, e.g.
   `/<name>:hello`). Common metadata fields: `displayName`, `description`,
   `version`, `author`, `homepage`, `repository`, `license`, `keywords`.
2. Add the plugin's content at the plugin root (not inside
   `.claude-plugin/` — that directory holds only `plugin.json`):
   - `skills/<skill-name>/SKILL.md` — Agent Skills, model-invoked based on
     their frontmatter `description`. A plugin with exactly one skill can
     place `SKILL.md` directly at the plugin root instead.
   - `commands/` — flat-markdown skills (legacy form; prefer `skills/`)
   - `agents/` — custom subagent definitions
   - `hooks/hooks.json` — event handlers
   - `.mcp.json` — MCP server configs
   - `.lsp.json` — LSP server configs
   - `monitors/monitors.json` — background monitors
   - `bin/` — executables added to the Bash tool's `PATH` while enabled
   - `settings.json` — default settings applied when the plugin is enabled
   - A skill can bundle a helper script alongside its `SKILL.md` for
     mechanics that should be deterministic rather than left to the model's
     judgment (e.g. config/manifest handling). Resolve it via
     `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/<file>`, never a hardcoded path.
3. Register the plugin in `.claude-plugin/marketplace.json`'s `plugins`
   array (`name`, `source`, `description`). Without this step nothing can
   discover the plugin even if it's fully built.

## Versioning plugins

A plugin's effective version is resolved in this order: `version` in its
`plugin.json` → `version` in its marketplace entry → the git commit SHA →
`unknown`.

- **Explicit version** (set `version` in `plugin.json`, semver
  `MAJOR.MINOR.PATCH`): users only get updates when the field is bumped.
  Pushing commits without bumping it does nothing — `/plugin update` will
  report it's already current. Use for plugins with a deliberate release
  cycle.
- **Commit-SHA version** (omit `version`): every new commit is treated as a
  new version and gets picked up. Use while a plugin is under active,
  frequent iteration.

Don't mix the two within one plugin's lifecycle without intent — switching
from explicit back to omitted (or vice versa) changes update behavior for
existing installs.
