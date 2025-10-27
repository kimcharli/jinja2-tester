# Jinja2 Template Tester

A web application for testing and validating Jinja2 templates with support for multiple versions and file uploads.

## Features

- Template validation and rendering
- File upload support for templates and data
- JSON and YAML data format support
- Error handling and validation feedback
- Responsive web interface

## Prerequisites

- Python 3.8 or higher
- `uv` package installer

## Project Setup

1. Install `uv` if you haven't already:

```bash
pip install uv
```

2. Clone the repository:

```bash
git clone <repository-url>
cd jinja2-tester
```

## Running the Application

Start the Flask development server using `uv`:

```bash
uv run jinja2_tester
```

The application will be available at `http://localhost:5000`

## Project Structure

## Environment Variables

Create a `.env` file in the project root with the following variables:

```text
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
MAX_TEMPLATE_SIZE=50KB
MAX_FILE_UPLOAD_SIZE=5MB
EXECUTION_TIMEOUT=5
```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Enter or upload a Jinja2 template
3. Enter or upload JSON/YAML data
4. Click "Validate and Render" to process the template
5. View the validation results and rendered output

## Supported File Types

### Templates

- `.j2`
- `.jinja`
- `.jinja2`
- `.html`
- `.txt`

### Data

- `.json`
- `.yaml`
- `.yml`

## Development

To contribute to the project:

1. Create a new branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:

```bash
git commit -m "Add your feature description"
```

3. Push to your branch:

```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
