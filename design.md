# Jinja2 Template Tester - Design Document

## 1. Overview

The Jinja2 Template Tester is a web application that allows users to validate and test Jinja2 templates in real-time. Users can input template code and test data to see how their templates will render.

## 2. Objectives

- Provide a user-friendly interface for testing Jinja2 templates
- Validate template syntax
- Allow users to input test data in JSON format
- Display rendered output and error messages clearly
- Ensure secure template processing
- Provide real-time side-by-side preview of rendered output

## 3. Technical Requirements

### 3.1 Backend Requirements

- Python 3.8+
- Flask web framework
- Jinja2 templating engine
- JSON parsing capabilities
- Error handling middleware

### 3.2 Frontend Requirements

- HTML5
- CSS3
- Responsive design
- Modern browser compatibility
- Split-panel layout
- Real-time rendering

## 4. Features

### 4.1 Core Features

1. Template Input
   - Multi-line text area for Jinja2 template code
   - File upload support for templates
   - File download capability
   - Syntax highlighting (future enhancement)
   - Template persistence across form submissions
   - Jinja version selection (2.7 through 3.x)
   - Whitespace control options:
     - Manual control using `-` in delimiters
     - Automatic trimming configuration
     - Toggle buttons for trim_blocks/lstrip_blocks

2. Data Input
   - Multiple format support (JSON/YAML)
   - Format auto-detection
   - Format conversion (JSON ↔ YAML)
   - Real-time format validation
   - Format-specific file handling
   - Pretty formatting capability
   - File upload/download with format preservation

3. Template Processing
   - Syntax validation
   - Safe rendering
   - Sandboxed execution environment
   - Real-time preview
   - Multi-format data support

4. Output Display
   - Side-by-side rendered preview
   - Error messages with line numbers
   - Clear success/failure indicators
   - Responsive layout
   - Output download functionality

### 4.2 UI Layout

1. Main Container
   - Maximum width: 1400px
   - White background
   - Rounded corners
   - Subtle shadow

2. Split Layout
   - Left panel: Input sections
   - Right panel: Output preview
   - Responsive design (stacks on mobile)
   - Minimum height: 600px

3. Input Sections
   - Template input area
   - Data input area
   - File upload buttons
   - Validation button
   - Status messages

4. Output Section
   - Fixed position
   - Auto-scrolling
   - Monospace font
   - Placeholder for empty state
   - Pre-formatted text display

### 4.3 Styling

1. Color Scheme
   - Primary button: #007bff
   - Secondary button: #6c757d
   - Success message: #d4edda / #155724
   - Error message: #f8d7da / #721c24
   - Borders: #ddd
   - Background: #f5f5f5
   - Text: #333, #444

2. Typography
   - Base font: Arial, sans-serif
   - Code font: Monospace
   - Headings: Color #333/#444
   - Placeholder text: Italic, #6c757d

3. Components
   - Buttons: Rounded corners, hover effects
   - Text areas: Monospace, resizable
   - Messages: Colored backgrounds, borders
   - Panels: Clear separation, borders

4. Responsive Behavior
   - Breakpoint: 1024px
   - Stack panels vertically on mobile
   - Adjust heights for mobile view
   - Maintain padding and spacing

### 4.4 File Operations

1. Download Features
   - Template download as .j2 files
   - Data download as formatted JSON
   - Rendered output download as text
   - Timestamp-based unique filenames
   - Content validation before download

2. Upload Features
   - Template file upload (.j2, .jinja, .jinja2, .html, .txt)
   - Data file upload (.json, .yaml, .yml)
   - File content validation
   - Error handling for invalid files

3. File Naming Convention

   ```text
   Templates: template-{timestamp}.j2
   Data: data-{timestamp}.json
   Output: rendered-output-{timestamp}.txt
   ```

4. Content Types

   ```text
   Templates: text/plain
   Data: application/json
   Output: text/plain
   ```

### 4.4 Data Format Intelligence

1. Format Selection
   - Dropdown for format selection (JSON/YAML)
   - Automatic format detection
   - Format conversion on selection change
   - Format validation feedback

2. Format Processing
   - JSON parsing and validation
   - YAML parsing and validation
   - Bidirectional conversion
   - Pretty printing
   - Error handling

3. File Operations
   - Format-specific file extensions
   - Format detection from file extension
   - Format-appropriate content-type
   - Format preservation during download

4. Format Features

   ```text
   JSON:
   - Strict syntax validation
   - Pretty printing with 2-space indent
   - Standard JSON file extension
   - application/json content type

   YAML:
   - Flexible syntax support
   - 2-space indentation
   - No reference aliases
   - Sorted keys
   - .yml/.yaml extensions
   - application/x-yaml content type
   ```

### 4.5 Format Conversion Specifications

1. JSON to YAML Conversion

   ```javascript
   {
     indent: 2,
     lineWidth: -1,
     noRefs: true,
     sortKeys: true
   }
   ```

2. YAML to JSON Conversion

   ```javascript
   {
     indent: 2,
     preserveOrder: false
   }
   ```

3. Format Detection Logic

   ```javascript
   function detectDataFormat(content) {
     1. Try JSON.parse()
     2. If fails, try YAML.load()
     3. If both fail, return null
   }
   ```

## 5. Security Considerations

### 5.1 Input Validation

- Sanitize all user inputs
- Limit template size
- Validate JSON data structure
- Implement CSRF protection

### 5.2 Template Execution

- Sandbox environment for template rendering
- Restricted access to system functions
- Timeout limits for template execution

## 6. API Design

### 6.1 Routes

```python
POST /
- Purpose: Process template and data
- Input: 
  - template: str or file
  - data: JSON str or file
  - jinja_version: str
  - trim_blocks: bool  # New option
  - lstrip_blocks: bool  # New option
- Output:
  - result: str
  - is_valid: bool
  - rendered_output: str
  - jinja_version: str

POST /upload-template
- Purpose: Handle template file uploads
- Input:
  - template_file: File
- Output:
  - template_content: str
  - error: Optional[str]

POST /upload-data
- Purpose: Handle data file uploads
- Input:
  - data_file: File
- Output:
  - data_content: str
  - error: Optional[str]
```

### 6.2 File Upload Specifications

- Supported template extensions: .j2, .jinja, .jinja2, .html, .txt
- Supported data file extensions: .json, .yaml, .yml, .csv
- Maximum file size: 5MB
- File content validation before processing

### 6.3 Supported Jinja Versions

- Jinja 2.7.x (Legacy)
- Jinja 2.8.x
- Jinja 2.9.x
- Jinja 2.10.x
- Jinja 2.11.x (LTS)
- Jinja 3.0.x
- Jinja 3.1.x (Latest)

## 7. Data Models

### 7.1 Template Request

```python
class TemplateRequest:
    template: str
    data: Dict[str, Any]
    jinja_version: str
```

### 7.2 Template Response

```python
class TemplateResponse:
    is_valid: bool
    result: str
    rendered_output: Optional[str]
    jinja_version: str
```

## 8. User Interface

### 8.1 Layout Components

- Header with application title
- Template input section
  - Text area for direct input
  - File upload button with drag-and-drop support
  - Jinja version selector dropdown
  - Version compatibility indicator
  - Whitespace control options:
    - Trim blocks toggle
    - Strip blocks toggle
    - Visual indicator for active options
- JSON data input section
  - Text area for direct input
  - File upload button with drag-and-drop support
  - Format selector for data files
- Submit button
- Results display area
- Rendered output section

### 8.2 Error Handling

- Visual feedback for validation errors
- Clear error messages
- Distinct styling for success/error states
- File upload error handling
  - Invalid file type
  - File size exceeded
  - File content validation errors

### 8.3 File Operation Controls

- Download buttons for each section
- Upload buttons for inputs
- Visual feedback for operations
- Error messages for invalid operations

### 8.5 Button Specifications

1. Primary Button
   - Validate and Render action
   - Full width
   - Blue background (#007bff)

2. Secondary Buttons
   - Upload/Download actions
   - Right-aligned in controls
   - Gray background (#6c757d)
   - Hover state (#5a6268)
   - Gap spacing between buttons

### 8.6 File Operation UI

1. Template Section
   - Download button
   - Upload button
   - File input (hidden)
   - Success/error feedback

2. Data Section
   - Download button
   - Upload button
   - File input (hidden)
   - JSON validation feedback

3. Output Section
   - Download button
   - Content availability check
   - Operation feedback

### 8.7 Data Format UI

1. Format Selector
   - Dropdown component
   - Current format indicator
   - Format change handler
   - Visual feedback on change

2. Format Button
   - Pretty print functionality
   - Format-specific formatting
   - Error feedback
   - Loading state

3. Visual Indicators
   - Format validation status
   - Conversion success/failure
   - Format-specific styling
   - Error messages

## 9. Future Enhancements

### 9.1 Planned Features

1. Syntax highlighting for template input
2. Template saving and sharing
3. Common template examples
4. JSON schema validation
5. Multiple template testing
6. Template performance metrics

### 9.2 Technical Improvements

1. API endpoint for programmatic access
2. Template caching
3. User accounts for saving templates
4. Template version control
5. Export functionality

## 10. Testing Strategy

### 10.1 Unit Tests

- Template parsing
- JSON validation
- Error handling
- Security measures

### 10.2 Integration Tests

- Form submission
- Template rendering
- Error reporting
- Security features

## 11. Deployment

### 11.1 Requirements

- Python environment
- Web server (e.g., Gunicorn)
- Reverse proxy (e.g., Nginx)
- SSL certificate
- Temporary file storage for uploads
- Multiple Jinja versions installed in isolated environments

### 11.2 Environment Variables

```text
FLASK_ENV=production
SECRET_KEY=<secure-key>
MAX_TEMPLATE_SIZE=50KB
MAX_FILE_UPLOAD_SIZE=5MB
EXECUTION_TIMEOUT=5
ALLOWED_TEMPLATE_EXTENSIONS=.j2,.jinja,.jinja2,.html,.txt
ALLOWED_DATA_EXTENSIONS=.json,.yaml,.yml,.csv
UPLOAD_FOLDER=/tmp/jinja2-tester
DEFAULT_JINJA_VERSION=3.1.2
SUPPORTED_JINJA_VERSIONS=2.7.3,2.8.1,2.9.6,2.10.3,2.11.3,3.0.3,3.1.2
```

### 11.3 Version Management

- Docker containers for each Jinja version
- Virtual environments for version isolation
- Version compatibility matrix
- Automatic version detection for templates
- Version-specific feature flags

## 12. Maintenance

### 12.1 Monitoring

- Error logging
- Usage metrics
- Performance monitoring
- Security auditing
- Version usage statistics

### 12.2 Updates

- Regular security patches
- Dependency updates
- Feature additions
- Bug fixes
- New Jinja version support
- Version deprecation management

## 13. UI Components Specification

### 13.1 HTML Structure

```html
<div class="main-container">
    <h1>Title</h1>
    <div class="split-layout">
        <div class="left-panel">
            <!-- Input sections -->
        </div>
        <div class="right-panel">
            <!-- Output section -->
        </div>
    </div>
</div>
```

### 13.2 CSS Architecture

- Mobile-first approach
- Flexbox layout system
- BEM naming convention
- Responsive breakpoints
- Consistent spacing system
- Component-based organization

### 13.3 Interactive Elements

- File upload buttons
- Validation button
- Real-time preview
- Error/success messages
- Responsive text areas
- Drag-and-drop support (future)

## 16. File Operations Specification

### 16.1 Download Operations

```javascript
function downloadFile(content, filename, contentType) {
    // Create blob from content
    // Generate download URL
    // Trigger download
    // Clean up resources
}
```

### 16.2 Content Validation

1. Template Download
   - Non-empty content check
   - File extension: .j2
   - Content type: text/plain

2. Data Download
   - Non-empty content check
   - JSON validation
   - Pretty formatting
   - File extension: .json
   - Content type: application/json

3. Output Download
   - Content existence check
   - Non-empty validation
   - File extension: .txt
   - Content type: text/plain

### 16.3 Error Handling

1. Download Errors
   - Empty content validation
   - Invalid JSON formatting
   - User feedback messages
   - Operation cancellation

2. Upload Errors
   - File type validation
   - Content parsing
   - Size limitations
   - User feedback messages

### 16.4 Security Considerations

1. Download Security
   - Content sanitization
   - File type verification
   - Resource cleanup

2. Upload Security
   - File type restrictions
   - Size limitations
   - Content validation
   - Sanitization of file names

This design document now includes comprehensive specifications for file operations, including download functionality for templates, data, and rendered output. The document covers UI components, error handling, security considerations, and implementation details.

This design document provides a comprehensive guide for building and maintaining the Jinja2 Template Tester web application, with detailed specifications for both functionality and user interface.

## 17. Data Format Handling

### 17.1 Backend Processing

```python
def process_data(content, format):
    if format == 'json':
        return json.loads(content)
    else:
        return yaml.safe_load(content)
```

### 17.2 Format Validation

```python
def validate_format(content, format):
    try:
        if format == 'json':
            json.loads(content)
        else:
            yaml.safe_load(content)
        return True, None
    except Exception as e:
        return False, str(e)
```

### 17.3 Format Conversion

```python
def convert_format(data, target_format):
    if target_format == 'json':
        return json.dumps(data, indent=2)
    else:
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=True,
            indent=2
        )
```

### 17.4 Error Handling

1. Validation Errors
   - Invalid syntax
   - Unsupported types
   - Conversion failures
   - File format mismatches

2. User Feedback
   - Clear error messages
   - Format-specific hints
   - Conversion status
   - Recovery suggestions

This design document now includes comprehensive specifications for data format intelligence, including format detection, conversion, validation, and error handling. The document covers both frontend and backend implementations, UI components, and user interaction patterns.
