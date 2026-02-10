# Linting Setup Guide

Prompt for AI agents to reproduce the linting and pre-commit hook setup in a new environment.

## Prerequisites

- Python project using `uv` as package manager
- `pyproject.toml` exists
- Git repository initialized

## Steps

### 1. Add dev dependencies to `pyproject.toml`

```toml
[dependency-groups]
dev = [
    "ruff>=0.8",
    "mdformat>=0.7",
    "mdformat-gfm>=0.3",
]
```

Then run `uv sync` to install.

### 2. Configure ruff in `pyproject.toml`

```toml
[tool.ruff]
src = ["src"]
target-version = "py313"  # match .python-version

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

- `E` = pycodestyle errors (line length, whitespace, etc.)
- `F` = pyflakes (unused imports, undefined names, etc.)
- `I` = isort (import ordering)
- `W` = pycodestyle warnings

### 3. Configure markdownlint for VSCode in `.markdownlint.json`

```json
{
  "MD029": {
    "style": "one"
  }
}
```

This aligns VSCode's markdownlint extension with mdformat's output style (all ordered list items use `1.`).

### 4. Create git pre-commit hook at `.git/hooks/pre-commit`

```bash
#!/usr/bin/env bash
set -e

# Get staged Python files
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -n "$STAGED_PY" ]; then
    echo "Running ruff check on staged Python files..."
    uv run ruff check --fix $STAGED_PY

    echo "Running ruff format on staged Python files..."
    uv run ruff format $STAGED_PY

    # Re-stage any files that were auto-fixed
    git add $STAGED_PY
    echo "Ruff checks passed."
fi

# Get staged Markdown files
STAGED_MD=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$' || true)

if [ -n "$STAGED_MD" ]; then
    echo "Running mdformat on staged Markdown files..."
    uv run mdformat $STAGED_MD

    # Re-stage any files that were auto-fixed
    git add $STAGED_MD
    echo "Markdown checks passed."
fi
```

Make it executable: `chmod +x .git/hooks/pre-commit`

### 5. Run initial fix on existing files

```bash
uv run ruff check --fix src/
uv run ruff format src/
uv run mdformat docs/ README.md
```

## How it works

| Tool                 | Scope  | What it does                                           | Runs on    |
| -------------------- | ------ | ------------------------------------------------------ | ---------- |
| `ruff check --fix`   | `*.py` | Lint + auto-fix (unused imports, import order, etc.)   | pre-commit |
| `ruff format`        | `*.py` | Auto-format (quotes, whitespace, line length)          | pre-commit |
| `mdformat`           | `*.md` | Auto-format markdown (list prefixes, spacing, tables)  | pre-commit |
| `.markdownlint.json` | `*.md` | Configures VSCode markdownlint to match mdformat style | IDE        |

## Files involved

| File                    | Purpose                    | Tracked in git  |
| ----------------------- | -------------------------- | --------------- |
| `pyproject.toml`        | ruff config + dev deps     | Yes             |
| `.markdownlint.json`    | VSCode markdownlint config | Yes             |
| `.git/hooks/pre-commit` | Git hook script            | No (local only) |

## Note on `.git/hooks/pre-commit`

Git hooks live in `.git/hooks/` which is not tracked by git. Each developer must create the hook locally. To automate this, you can either:

1. Store the hook in a tracked location (e.g., `scripts/pre-commit`) and symlink it:
   ```bash
   ln -sf ../../scripts/pre-commit .git/hooks/pre-commit
   ```
1. Document it in the README for manual setup.
