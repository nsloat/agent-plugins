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
