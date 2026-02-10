# Jinja2 Tester - Repository Overview

Quick-reference for AI agents and contributors to understand this repo without reading every file.

## What This Is

A Flask web application for testing Jinja2 templates. Users paste (or upload) a Jinja2 template and JSON/YAML data, and the app renders the output in real time. Primary use case: testing Juniper Apstra network device configlets.

## Tech Stack

| Component | Details |
|-----------|---------|
| Language | Python 3.13 |
| Package manager | `uv` (always use `uv run` to execute) |
| Backend | Flask 2.3.3, Jinja2 3.1.2, PyYAML 6.0.1 |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Build | Hatchling |
| Entry point | `jinja2_tester.app:main` |

## Repository Structure

```
jinja2-tester/
├── src/jinja2_tester/          # Application source code
│   ├── app.py                  # Flask app: routes, rendering, validation (241 lines)
│   ├── static/
│   │   ├── script.js           # Frontend logic: AJAX rendering, uploads, format conversion (318 lines)
│   │   └── style.css           # Responsive split-panel styling (331 lines)
│   └── templates/
│       └── index.html          # Single-page UI: left panel (inputs), right panel (output)
├── apstra_configlets/          # 33 sample Jinja2 templates (Juniper Apstra network configs)
├── example/                    # Example template + data for stitched DCI border use case
│   └── stiched-dci-border/
│       ├── template.j2
│       ├── input_1.yaml
│       └── input_jcl_dc1.yaml
├── var/                        # Test data files (JSON contexts from Apstra)
│   ├── test.json               # ~492KB Apstra device context (48 top-level keys)
│   ├── border1-context.json
│   └── SNMP-Sflow.txt
├── docs/                       # Documentation
│   └── requirements.md         # Feature requirements and tracking
├── design.md                   # Detailed design specification
├── pyproject.toml              # Dependencies and build config
├── .env                        # Runtime config (SECRET_KEY, limits)
└── .python-version             # 3.13
```

## Key Architecture Decisions

### Backend (`app.py`)

- **Routes:**
  - `GET /` - Serve the single-page UI
  - `POST /` - Traditional form submission (render)
  - `POST /render` - AJAX endpoint for real-time rendering (returns JSON with `is_valid`, `result`, `rendered_output`, `status`)
  - `POST /upload-template` - File upload for `.j2`, `.jinja`, `.jinja2`, `.html`, `.txt`
  - `POST /upload-data` - File upload for `.json`, `.yaml`, `.yml`

- **Jinja2 Environment:** `jinja2.ext.do` extension enabled (Apstra-style `{% do %}` blocks), configurable `trim_blocks` and `lstrip_blocks`

- **Data parsing:** Tries JSON first, falls back to YAML via `yaml.safe_load()`

- **Size limits:** `MAX_CONTENT_LENGTH = 5MB`, `max_form_memory_size = 5MB` (Werkzeug default was 500KB, which silently blocked files >500KB)

- **Status metadata:** The `/render` endpoint returns a `status` object with `template_size`, `data_size`, `data_format`, `parse_time_ms`, `render_time_ms`, `output_size`, `warnings`

### Frontend (`script.js`)

- **Real-time rendering:** Debounced (500ms) AJAX calls to `/render` on every template/data input change
- **Format conversion:** Client-side JSON/YAML bidirectional conversion via `js-yaml` CDN library
- **Status button:** Color-coded (green/yellow/red/gray) with expandable panel showing render metadata
- **File uploads:** Template and data files uploaded via separate endpoints, results populate textareas

### CSS (`style.css`)

- Split-panel flexbox layout (left: inputs, right: output)
- Responsive breakpoint at 1024px (stacks vertically)
- Monospace fonts for code areas
- Color scheme: primary #007bff, success #28a745, warning #ffc107, error #dc3545

## Common Operations

```bash
# Run the app
uv run jinja2-tester

# Or directly
uv run python -m jinja2_tester.app

# Test rendering programmatically
uv run python -c "
from jinja2_tester.app import app
with app.test_client() as c:
    resp = c.post('/render', data={'template': '{{ name }}', 'data': '{\"name\": \"test\"}'})
    print(resp.get_json())
"
```

## Known Gotchas

1. **Werkzeug form field size limit:** Default `max_form_memory_size` is 500KB. Large JSON files (like `var/test.json` at 492KB) silently fail with HTTP 413. Fixed by setting `app.request_class.max_form_memory_size = 5MB`.

2. **Data format detection:** The app tries JSON parsing first. If the data is valid YAML but not valid JSON, it correctly falls back to YAML. However, the data format selector on the frontend is independent of server-side detection.

3. **js-yaml CDN dependency:** The frontend loads `js-yaml` from cdnjs at runtime for client-side YAML support. No local fallback exists.
