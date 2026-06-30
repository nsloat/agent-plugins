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
