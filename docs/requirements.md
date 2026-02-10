# Jinja2 Tester - Requirements

## REQ-001: Status Button for Error Visibility
**Status:** Implemented
**Priority:** High
**Date:** 2026-02-10

### Problem
When using large data files (e.g., `ospf.j2` + `test.json` at ~492KB), the web interface produces no output with no visible error feedback. The rendering works correctly in Python but the web UI silently fails, leaving users with no information about what went wrong.

### Requirements
1. **Status Button** - A button next to "Validate and Render" that shows rendering status details
2. **Status Panel** - Expandable panel showing:
   - Template size (bytes)
   - Data size (bytes) with warning for large inputs (>100KB)
   - Detected data format (JSON/YAML/invalid)
   - Parse time (ms)
   - Render time (ms)
   - Output size (bytes)
3. **Color-coded Status** - Button changes color based on state:
   - Gray: no render yet
   - Green: success
   - Yellow: warnings (e.g., large data size)
   - Red: error occurred
4. **Error Details** - Full error message displayed in the status panel
5. **Warnings** - Alert when data exceeds 100KB threshold

### Root Cause Found

Werkzeug (Flask's HTTP layer) has a default `max_form_memory_size` of 500,000 bytes (500KB).
The `test.json` file is 492,336 bytes raw, but exceeds 500KB once form-encoded, causing a
silent HTTP 413 error that was caught by the generic exception handler with no useful feedback.

**Fix:** Set `app.request_class.max_form_memory_size = 5 * 1024 * 1024` (5MB) to match the
existing `MAX_CONTENT_LENGTH` limit.

### Technical Notes

- Backend `/render` endpoint returns a `status` object with metadata
- Frontend updates status panel on each render response
- Network errors are also captured and shown in status

### Files Changed

- `src/jinja2_tester/app.py` - Added `max_form_memory_size`, `time` import, status metadata in `/render`
- `src/jinja2_tester/templates/index.html` - Added status button and expandable status panel
- `src/jinja2_tester/static/script.js` - Added `updateStatusPanel()`, status button toggle handlers
- `src/jinja2_tester/static/style.css` - Added styles for status button, panel, warnings, errors
