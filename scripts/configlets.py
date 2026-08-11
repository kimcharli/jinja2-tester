#!/usr/bin/env python3
"""Extract, validate, and report on Apstra configlet frontmatter headers.

Header format (see apstra_configlets/_header-example.j2):

    {#
    ---
    name: some-configlet
    ...
    ---
    free-form notes
    -#}

Usage:
    python scripts/configlets.py check     # validate headers, exit 1 on error
    python scripts/configlets.py readme    # regenerate apstra_configlets/README.md
    python scripts/configlets.py list      # dump parsed metadata as JSON
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGLET_DIR = REPO_ROOT / "apstra_configlets"
README = CONFIGLET_DIR / "README.md"

# Files prefixed with META_PREFIX are documentation or shared partials, not
# deployable configlets: they are skipped by every subcommand.
META_PREFIX = "_"
HEADER_EXAMPLE = "_header-example.j2"

HEADER_RE = re.compile(
    r"\A\{#-?\s*\n---\n(?P<meta>.*?)\n---\n(?P<notes>.*?)\n?-?#\}",
    re.S,
)

REQUIRED_KEYS = ("name", "summary", "config_style", "section", "status")
KNOWN_KEYS = {
    "name",
    "summary",
    "config_style",
    "section",
    "roles",
    "category",
    "status",
    "requires",
    "tested_on",
    "refs",
    "author",
    "updated",
    "changelog",
}

CONFIG_STYLES = {"junos", "eos", "nxos", "cumulus", "sonic"}
SECTIONS = {
    "top_level_set_delete",
    "top_level_hierarchical",
    "system",
    "interface",
    "file",
    "frr",
    "ospf",
    "set_based_system",
    "set_based_interface",
    "delete_based_interface",
}
ROLES = {"spine", "leaf", "access", "all"}
STATUSES = {"example", "active", "not-applied", "incomplete"}
CATEGORIES = {"essential", "conditional", "optional", "misc"}

CATEGORY_TITLES = [
    ("essential", "Essential (Always)", "Considered essential for basic operation."),
    (
        "conditional",
        "Essential (In Certain Cases)",
        "Essential under specific circumstances.",
    ),
    ("optional", "Optional", "Optional functionality."),
    ("misc", "Miscellaneous", "Other configlets for various purposes."),
]


@dataclass
class Configlet:
    path: Path
    meta: dict | None = None
    notes: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def has_header(self) -> bool:
        return self.meta is not None

    @property
    def category(self) -> str:
        return (self.meta or {}).get("category") or "misc"

    @property
    def summary(self) -> str:
        return (self.meta or {}).get("summary") or ""


def parse(path: Path) -> Configlet:
    cfg = Configlet(path=path)
    text = path.read_text(encoding="utf-8")

    match = HEADER_RE.match(text)
    if not match:
        return cfg

    try:
        meta = yaml.safe_load(match.group("meta"))
    except yaml.YAMLError as exc:
        cfg.errors.append(f"frontmatter is not valid YAML: {exc}")
        return cfg

    if not isinstance(meta, dict):
        cfg.errors.append("frontmatter must be a YAML mapping")
        return cfg

    cfg.meta = meta
    cfg.notes = match.group("notes").strip()

    if "-#}" in text[match.end() :]:
        cfg.errors.append(
            "header appears truncated: a comment-closing sequence inside the header "
            "ended the Jinja comment early, leaking the rest into rendered config"
        )
    if not text[: match.end()].rstrip().endswith("-#}"):
        cfg.warnings.append(
            "close the header with the whitespace-stripping form to avoid a "
            "leading blank line in rendered config"
        )

    return cfg


def validate(cfg: Configlet) -> None:
    """Populate cfg.errors / cfg.warnings. Assumes parse() already ran."""
    if not cfg.has_header:
        if not cfg.errors:
            cfg.warnings.append("no frontmatter header (legacy style)")
        return

    meta = cfg.meta
    assert meta is not None

    for key in REQUIRED_KEYS:
        if not meta.get(key):
            cfg.errors.append(f"missing required key: {key}")

    for key in meta:
        if key not in KNOWN_KEYS:
            cfg.warnings.append(f"unknown key: {key}")

    if meta.get("name") and meta["name"] != cfg.stem:
        cfg.errors.append(
            f"name {meta['name']!r} does not match filename stem {cfg.stem!r}"
        )

    _check_enum(cfg, "config_style", CONFIG_STYLES)
    _check_enum(cfg, "section", SECTIONS)
    _check_enum(cfg, "status", STATUSES)
    _check_enum(cfg, "category", CATEGORIES, required=False)

    roles = meta.get("roles")
    if roles is not None:
        if not isinstance(roles, list):
            cfg.errors.append("roles must be a list")
        else:
            for role in roles:
                if role not in ROLES:
                    cfg.errors.append(
                        f"invalid role {role!r} (expected one of {sorted(ROLES)})"
                    )

    if "category" not in meta:
        cfg.warnings.append("no category; will be grouped under Miscellaneous")

    updated = meta.get("updated")
    if updated is not None and not isinstance(updated, datetime.date):
        cfg.errors.append("updated must be an unquoted YAML date (YYYY-MM-DD)")

    for key in ("tested_on", "refs", "changelog"):
        value = meta.get(key)
        if value is not None and not isinstance(value, list):
            cfg.errors.append(f"{key} must be a list")

    requires = meta.get("requires")
    if requires is not None:
        if not isinstance(requires, dict):
            cfg.errors.append("requires must be a mapping with 'vars' and/or 'tags'")
        else:
            for key in requires:
                if key not in {"vars", "tags"}:
                    cfg.warnings.append(f"unknown requires key: {key}")

    for ref in meta.get("refs") or []:
        if isinstance(ref, str) and not ref.startswith(("http://", "https://")):
            cfg.warnings.append(f"ref is not a URL: {ref}")


def _check_enum(
    cfg: Configlet, key: str, allowed: set[str], required: bool = True
) -> None:
    value = (cfg.meta or {}).get(key)
    if value is None:
        return
    if value not in allowed:
        level = cfg.errors if required else cfg.warnings
        level.append(f"invalid {key} {value!r} (expected one of {sorted(allowed)})")


def collect() -> list[Configlet]:
    configlets = []
    for path in sorted(CONFIGLET_DIR.glob("*.j2")):
        if path.name.startswith(META_PREFIX):
            continue
        cfg = parse(path)
        validate(cfg)
        configlets.append(cfg)
    return configlets


def cmd_check(configlets: list[Configlet]) -> int:
    errors = sum(len(c.errors) for c in configlets)
    warnings = sum(len(c.warnings) for c in configlets)
    migrated = sum(1 for c in configlets if c.has_header)

    for cfg in configlets:
        for msg in cfg.errors:
            print(f"ERROR   {cfg.filename}: {msg}")
        for msg in cfg.warnings:
            print(f"warning {cfg.filename}: {msg}")

    print()
    print(f"{migrated}/{len(configlets)} configlets have a frontmatter header")
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def cmd_list(configlets: list[Configlet]) -> int:
    payload = [
        {
            "file": cfg.filename,
            "meta": cfg.meta,
            "notes": cfg.notes,
            "errors": cfg.errors,
            "warnings": cfg.warnings,
        }
        for cfg in configlets
    ]
    print(json.dumps(payload, indent=2, default=str))
    return 0


def cmd_readme(configlets: list[Configlet]) -> int:
    lines = [
        "# Configlets",
        "",
        "<!-- Generated by scripts/configlets.py readme. Do not edit by hand.",
        "     Edit the frontmatter header in each .j2 file, then regenerate. -->",
        "",
        "Originally from <https://github.com/kimcharli/ck-apstra-api>,",
        "moved here for better coherency within this project.",
        "",
        f"See `{HEADER_EXAMPLE}` for the header format.",
        "",
    ]

    described = [c for c in configlets if c.has_header]
    legacy = [c for c in configlets if not c.has_header]

    for key, title, blurb in CATEGORY_TITLES:
        members = [c for c in described if c.category == key]
        if not members:
            continue
        lines += [f"## {title}", "", blurb, ""]
        for cfg in sorted(members, key=lambda c: c.filename):
            lines.append(f"- `{cfg.filename}` — {cfg.summary}{_annotations(cfg)}")
        lines.append("")

    if legacy:
        lines += [
            "## Unclassified (legacy header)",
            "",
            "These still use ad hoc Jinja comment headers and have not been migrated.",
            "",
        ]
        lines += [
            f"- `{cfg.filename}`" for cfg in sorted(legacy, key=lambda c: c.filename)
        ]
        lines.append("")

    README.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(
        f"wrote {README.relative_to(REPO_ROOT)}: "
        f"{len(described)} described, {len(legacy)} legacy"
    )
    return 0


def _annotations(cfg: Configlet) -> str:
    meta = cfg.meta or {}
    bits = []
    roles = meta.get("roles")
    if roles:
        bits.append("/".join(roles))
    status = meta.get("status")
    if status and status != "active":
        bits.append(status)
    return f" ({', '.join(bits)})" if bits else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["check", "readme", "list"])
    args = parser.parse_args()

    if not CONFIGLET_DIR.is_dir():
        print(f"configlet directory not found: {CONFIGLET_DIR}", file=sys.stderr)
        return 2

    configlets = collect()
    commands = {"check": cmd_check, "readme": cmd_readme, "list": cmd_list}
    return commands[args.command](configlets)


if __name__ == "__main__":
    raise SystemExit(main())
