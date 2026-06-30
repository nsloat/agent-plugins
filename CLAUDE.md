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

## Architecture

Each plugin is a standalone directory under `plugins/<name>/`:

- `plugins/<name>/.claude-plugin/plugin.json` — manifest (`name`,
  `displayName`, `description`, `version`). This is plugin metadata only;
  marketplace registration is separate (see below).
- `plugins/<name>/skills/<skill>/SKILL.md` — the actual skill: YAML
  frontmatter (`name`, `description`, `user-invocable`, `allowed-tools`)
  followed by instructions for the agent. **The `description` field is the
  trigger** — Claude decides whether to invoke a skill based on it, so it
  must spell out the literal phrases/situations that should fire it (see
  `plugins/project/skills/project/SKILL.md`'s description for the pattern).
- A skill can bundle a helper script next to its `SKILL.md` for mechanics
  that should be deterministic rather than left to the model's judgment —
  e.g. `plugins/project/skills/project/project_tool.py` handles config,
  manifest, and discovery logic for the `project` skill. Resolve such a
  script from inside a SKILL.md via `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/<file>`,
  never a hardcoded path.

Adding a plugin to the marketplace is a **separate step** from creating it:
the plugin directory must also be added to the `plugins` array in
`.claude-plugin/marketplace.json` (`name`, `source`, `description`), or
nothing can discover it.

Two plugins exist today:
- `hello-world` — minimal example, no helper script, demonstrates the
  smallest valid plugin+skill shape.
- `project` — manages multi-repo "projects" (one git worktree per repo
  under a shared branch, from setup through finish); its logic that must be
  exact (config validation, manifest shape, branch resolution, worktree
  safety checks) lives in `project_tool.py` rather than in the SKILL.md
  prose.

## Commands

Run a plugin's tests from its skill directory, e.g.:

```
cd plugins/project/skills/project && python3 -m pytest
```

There is no repo-wide build/lint step — each plugin's tooling is scoped to
that plugin's own skill directory.
