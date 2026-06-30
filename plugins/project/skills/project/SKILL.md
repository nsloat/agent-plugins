---
name: project
description: Manage multi-repo "projects" — a named effort with one git worktree per repo under <projects_root>/<name>/. Use to start, add repos to, check status of, push, or finish a project; or to bootstrap the workflow on a new machine. Triggers on "/project", "new project", "start a project", "add <repo> to the project", "project status", "finish the project", "set up projects workflow".
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Project Workflow

Manage multi-repo efforts. A **project** lives at `<projects_root>/<name>/` and
holds one real git worktree per repo it touches, all on a shared branch. The
deterministic mechanics live in the bundled `project_tool.py`; this skill
orchestrates git and `gh`, calling the helper for config, manifest, discovery,
AGENTS.md injection, and finish-safety.

`project_tool.py` is bundled alongside this SKILL.md in the plugin. Resolve it
via the plugin root:

```bash
HELPER="${CLAUDE_PLUGIN_ROOT}/skills/project/project_tool.py"
```

Invoke as `python3 "$HELPER" <subcommand> ...`.

## Config

All user-specific values live in `~/.config/projects/config.json`. Load it at the
start of every subcommand except `setup`. If it is missing, tell the user to run
`/project setup` first.

## Subcommands

Dispatch on the first argument: `setup`, `new`, `add`, `status`, `push`, `finish`.
If no argument is given, infer the current project from the working directory
(walk up to find a dir containing `.project.json`) and show `status`.

### setup
Run-once bootstrap. Makes the workflow usable on a fresh machine or by a teammate.

1. Ask the user where their repos are checked out (`repos_root`). There is no
   universal default — confirm the actual path.
2. `python3 "$HELPER" discover-repos --root <repos_root>` → show the detected
   repos; let the user prune the list.
3. Ask for `branch_namespace` (their branch prefix, e.g. `alice-co`).
4. Ask the user to define `signal_rules`: keyword lists that map to specific repos.
   For each repo discovered in step 2, offer to let them assign keywords. Example:
   `{"match": ["terraform", "infra"], "repo": "ops-infra"}`. There are no
   hardcoded defaults — every team's repo names and keywords differ.
5. Build the config object and write it: assemble JSON with `repos_root`,
   `projects_root` (suggest `<repos_root>/projects` or ask), `branch_namespace`,
   `agents_md_path` (default `~/AGENTS.md`), the pruned `repos`, and
   `signal_rules`; write with Write, then `python3 "$HELPER" validate-config`.
6. `python3 "$HELPER" inject-agents-md` — idempotently add the projects-workflow
   block to the user's AGENTS.md.
7. Create `projects_root` if missing (`mkdir -p`).
8. Report what was written.

### new <name> [--category X] [--ticket KEY ...]
1. Load config.
2. Resolve `category`: if `--category` given use it; else if `--ticket` given use
   the first ticket key; else prompt.
3. If `--ticket` given and a ticket-tracker MCP is available, read each ticket to
   collect description text for repo-suggestion heuristics.
4. Resolve the branch: `python3 "$HELPER" resolve-branch --namespace <ns>
   --category <cat> --name <name>`.
5. Suggest repos: apply the `signal_rules` from config to any collected ticket
   text. Always include the user's primary repo (ask if unsure). Present the
   suggested set; the user confirms/edits.
6. Create the project dir and write `.project.json` (use `create_manifest` shape;
   set `created` to today's date). For each chosen repo, create a worktree:
   - Prefer native worktree tooling **only if** it can target
     `<projects_root>/<name>/<repo>`; otherwise:
     `git -C <repo_path> worktree add -b <branch> <projects_root>/<name>/<repo> <base>`
   - Append the repo entry (`name`, `base`, `branch`) to the manifest.
7. Print the project path and the per-repo worktree paths.

### add <repo> [--project <name>]
1. Load config + the project manifest (infer project from cwd if `--project`
   omitted).
2. Look up `<repo>` in config (`path`, `base`). If absent, error with the known
   repo names.
3. Create the worktree exactly as in `new` step 6, using the manifest's shared
   `branch`. Append to the manifest.

### status [--project <name>]
For each repo in the manifest, in its worktree, report:
- current branch, dirty? (`git status --porcelain`), ahead/behind upstream
  (`git rev-list --left-right --count @{u}...HEAD`, or "no upstream"),
- PR state via `gh pr view --json state,url 2>/dev/null` (or "no PR").
Print a per-repo table.

### push [--project <name>]
For each repo in the manifest: prefer native push if available, else
`git -C <worktree> push -u origin <branch>`. Report per repo.

### finish [--project <name>] [--force]
For each repo in the manifest, gather status: `dirty`, `unpushed`, `pr_merged`
(via `gh pr view --json state` → merged?). Decide removal with the helper's
`repo_safe_to_remove({dirty, unpushed, pr_merged, force})`.
- Safe → `git -C <repo_path> worktree remove <worktree>` (add `--force` only if
  `--force` was passed).
- Unsafe → report why and skip.
Once all repos are removed, delete the project directory. Print a per-repo summary
of removed vs skipped.

## Notes
- Never delete a worktree that is dirty or unpushed unless `--force`.
- All paths come from config; nothing is hardcoded to a particular user.
