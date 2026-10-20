# Apstra Configlets Guide (`apstra_configlets/`)

Rules and conventions for authoring, editing, and validating Jinja2 configlets in this directory.

## 1. Frontmatter Header Standard

Every deployable `.j2` file must start with a YAML frontmatter block inside a Jinja comment (`{# ... -#}`). See `_header-example.j2` for the canonical template.

```jinja2
{#
---
name: <filename-stem>                # Required: must match filename without .j2
summary: <one-line description>      # Required
config_style: junos                  # Required: junos | eos | nxos | cumulus | sonic
section: top_level_set_delete        # Required: top_level_set_delete | top_level_hierarchical | system | interface | file | frr | ospf | set_based_system | set_based_interface | delete_based_interface
roles: [leaf]                        # spine | leaf | access | all
category: misc                       # essential | conditional | optional | misc
status: active                       # Required: active | example | not-applied | incomplete
requires:
  vars: [system_tags, security_zones, vxlan, vlan]
  tags: [ospf, ospf/passive]
tested_on: ["6.1.2-28"]
refs:
  - https://...
author: kimcharli@gmail.com
updated: 2026-10-20                  # Unquoted YYYY-MM-DD
changelog:
  - 2026-10-20 short note
---
Free-form notes: tag contracts, platform caveats, verification commands.
-#}
```

- **Never** include the comment-closing sequence inside the header body (it truncates the comment and leaks metadata into rendered device config).
- **Always** close the frontmatter header with `-#}` to strip leading blank lines.
- Files prefixed with `_` (e.g., `_header-example.j2`) are meta/partials and skipped by `scripts/configlets.py`.

## 2. Apstra Validator & Jinja2 Rendering Rules

1. **Hoist `{% set %}` to the top level:**
   - Define constants (`{% set TAG = '...' %}`) at the top of the template, **outside** any `{% if %}` block.
   - Apstra's configlet validator flags variables assigned inside an `{% if %}` as missing device-context variables.
   - Use `namespace()` when mutating state inside `{% for %}` loops.

2. **No Line Wrapping (`{% ... %}` or CLI `set` statements):**
   - Keep each `{% if ... %}`, `{% for ... %}`, `{% set ... | ... %}` pipeline, and rendered CLI `set`/`delete` statement on a **single line**, even when it exceeds typical column limits (e.g. the long `{% if vn.vrf_name == sz_name ... %}` filter in `ospf-tags.j2`).
   - Wrapping Jinja control tags or CLI commands across multiple lines breaks Apstra rendering / Junos commit.

3. **Whitespace & Line-Break Control (`trim_blocks=True`, `lstrip_blocks=True`):**
   - Use `{%-` on the first control tag after top-level `{% set %}` statements so no leading blank line is emitted.
   - **Never** place `{#-` or `{%-` after a rendered configuration line. `{-` strips all preceding newlines while `trim_blocks` strips the trailing newline, concatenating adjacent CLI commands onto the same line. Use `{#` and `{%` instead, and avoid blank lines between consecutive `set` blocks.

4. **Do Not Mutate Apstra Context Dictionaries:**
   - Treat `interface`, `security_zones`, `vxlan`, `vlan`, and `system_tags` as read-only. Build derived collections in a `namespace()` rather than mutating native entries in place.

5. **Deterministic Output:**
   - Sort tag lists and dictionary iterations (`| sort`) where order is not semantically fixed so regenerated configs produce clean, stable diffs.

## 3. Validation & README Workflow

`apstra_configlets/README.md` is **auto-generated** from frontmatter headers. Never edit `README.md` by hand.

After adding or modifying any configlet:

```sh
mise run configlets-check
mise run configlets-readme
```
