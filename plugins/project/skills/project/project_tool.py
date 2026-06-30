#!/usr/bin/env python3
"""project_tool.py — deterministic helpers for the /project workflow skill."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

CONFIG_PATH = Path("~/.config/projects/config.json").expanduser()
BLOCK_START = "<!-- projects-workflow:start -->"
BLOCK_END = "<!-- projects-workflow:end -->"


def slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip())
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def resolve_branch(namespace: str, category: str, name: str) -> str:
    parts = [slugify(p) for p in (namespace, category, name) if p and p.strip()]
    return "/".join(parts)


REQUIRED_KEYS = [
    "repos_root",
    "projects_root",
    "branch_namespace",
    "agents_md_path",
    "repos",
    "signal_rules",
]


def load_config(path=CONFIG_PATH) -> dict:
    with open(Path(path).expanduser()) as f:
        return json.load(f)


def save_config(cfg: dict, path=CONFIG_PATH) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def validate_config(cfg: dict) -> list:
    errors = []
    for k in REQUIRED_KEYS:
        if k not in cfg:
            errors.append(f"missing key: {k}")
    if not cfg.get("branch_namespace"):
        errors.append("branch_namespace must be non-empty")
    for i, r in enumerate(cfg.get("repos", [])):
        for rk in ("name", "path", "base"):
            if rk not in r:
                errors.append(f"repos[{i}] missing {rk}")
    return errors


def is_git_repo(path) -> bool:
    return (Path(path).expanduser() / ".git").exists()


def default_branch(repo_path) -> str:
    repo = str(Path(repo_path).expanduser())
    try:
        out = subprocess.run(
            ["git", "-C", repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out.split("/", 1)[1] if "/" in out else out
    except subprocess.CalledProcessError:
        for b in ("main", "master"):
            r = subprocess.run(
                ["git", "-C", repo, "rev-parse", "--verify", "--quiet", b],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                return b
        head = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()
        return head or "main"


def discover_repos(repos_root) -> list:
    root = Path(repos_root).expanduser()
    repos = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if child.is_dir() and is_git_repo(child):
            repos.append({"name": child.name, "path": str(child), "base": default_branch(child)})
    return repos


def suggest_repos(text, signal_rules) -> list:
    text_l = (text or "").lower()
    hits = []
    for rule in signal_rules or []:
        if any(kw.lower() in text_l for kw in rule.get("match", [])):
            if rule["repo"] not in hits:
                hits.append(rule["repo"])
    return hits


def render_agents_block(cfg: dict) -> str:
    projects_root = cfg.get("projects_root", "~/projects")
    ns = cfg.get("branch_namespace", "")
    lines = [
        BLOCK_START,
        "## Required Workflow for New Tasks (Projects Paradigm)",
        "",
        f"All implementation work happens inside a **project** under `{projects_root}/`.",
        "A project is a named logical effort that may span multiple repos and tickets;",
        "each project directory holds one real git worktree per repo it touches.",
        "",
        "1. **Start:** `/project new <name>` — creates the project dir, resolves the",
        f"   shared branch `{ns}/<category>/<name>`, suggests repos, and creates a",
        "   worktree per chosen repo.",
        "2. **Add a repo on demand:** `/project add <repo>`.",
        f"3. **Work** inside `{projects_root}/<name>/<repo>/` — each subdir is a real",
        "   worktree, so grep/build/test run natively.",
        "4. **Status:** `/project status`. **Push:** `/project push`.",
        "5. **Finish:** `/project finish` — per-repo-aware teardown.",
        "",
        "Worktrees are created via native agent worktree tooling when it can target the",
        "project path, otherwise via the git CLI. There is no `wt-*` flow.",
        BLOCK_END,
    ]
    return "\n".join(lines)


def inject_block(content: str, block: str) -> str:
    if BLOCK_START in content and BLOCK_END in content:
        pattern = re.compile(
            re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), re.DOTALL
        )
        return pattern.sub(lambda _m: block, content)
    if content == "":
        return block + "\n"
    sep = "\n" if content.endswith("\n") else "\n\n"
    if content.endswith("\n\n"):
        sep = ""
    return content + sep + block + "\n"
