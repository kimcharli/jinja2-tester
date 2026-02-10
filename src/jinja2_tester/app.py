from flask import Flask, render_template, request, jsonify
from jinja2 import Environment, meta, exceptions
import json
import yaml
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.request_class.max_form_memory_size = 5 * 1024 * 1024  # 5MB max form field size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

ALLOWED_TEMPLATE_EXTENSIONS = {'.j2', '.jinja', '.jinja2', '.html', '.txt'}
ALLOWED_DATA_EXTENSIONS = {'.json', '.yaml', '.yml', '.csv'}

def is_allowed_template_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_TEMPLATE_EXTENSIONS

def is_allowed_data_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_DATA_EXTENSIONS

def validate_template(template_str, trim_blocks=True, lstrip_blocks=True):
    try:
        env = Environment(
            trim_blocks=trim_blocks,    # Removes first newline after a block
            lstrip_blocks=lstrip_blocks, # Strips tabs and spaces from the beginning of a line to the start of a block
            extensions=['jinja2.ext.do']
        )
        env.parse(template_str)
        return True, "Template syntax is valid"
    except exceptions.TemplateSyntaxError as e:
        return False, f"Template syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error validating template: {str(e)}"

def render_template_string(template_str, data, trim_blocks=True, lstrip_blocks=True):
    try:
        env = Environment(
            trim_blocks=trim_blocks,
            lstrip_blocks=lstrip_blocks,
            extensions=['jinja2.ext.do']
        )
        template = env.from_string(template_str)
        return True, template.render(**data)
    except Exception as e:
        return False, f"Error rendering template: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        template_input = request.form.get('template', '')
        data_input = request.form.get('data', '{}')
        trim_blocks = request.form.get('trim_blocks', 'true').lower() == 'true'
        lstrip_blocks = request.form.get('lstrip_blocks', 'true').lower() == 'true'
        
        # Validate template
        is_valid, result = validate_template(template_input, trim_blocks, lstrip_blocks)
        
        if is_valid:
            try:
                # Try parsing as JSON first, then YAML
                try:
                    data = json.loads(data_input)
                except json.JSONDecodeError:
                    try:
                        data = yaml.safe_load(data_input)
                    except yaml.YAMLError as e:
                        return render_template('index.html',
                                            template_input=template_input,
                                            data_input=data_input,
                                            is_valid=False,
                                            result=f"Invalid data format: {str(e)}")
                
                # Render template
                success, rendered = render_template_string(template_input, data, trim_blocks, lstrip_blocks)
                if success:
                    return render_template('index.html',
                                         template_input=template_input,
                                         data_input=data_input,
                                         is_valid=True,
                                         result="Template is valid",
                                         rendered_output=rendered)
                else:
                    return render_template('index.html',
                                         template_input=template_input,
                                         data_input=data_input,
                                         is_valid=False,
                                         result=rendered)
            except Exception as e:
                return render_template('index.html',
                                     template_input=template_input,
                                     data_input=data_input,
                                     is_valid=False,
                                     result=f"Error: {str(e)}")
        else:
            return render_template('index.html',
                                 template_input=template_input,
                                 data_input=data_input,
                                 is_valid=False,
                                 result=result)
    
    return render_template('index.html',
                         template_input='',
                         data_input='{}',
                         is_valid=None,
                         result=None)

@app.route('/upload-template', methods=['POST'])
def upload_template():
    if 'template_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['template_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not is_allowed_template_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        template_content = file.read().decode('utf-8')
        return jsonify({'template_content': template_content})
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'}), 400

@app.route('/upload-data', methods=['POST'])
def upload_data():
    if 'data_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['data_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not is_allowed_data_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        content = file.read().decode('utf-8')
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext in {'.json'}:
            data = json.loads(content)
            formatted_content = json.dumps(data, indent=2)
        elif ext in {'.yaml', '.yml'}:
            data = yaml.safe_load(content)
            formatted_content = yaml.dump(data, default_flow_style=False, sort_keys=True)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        return jsonify({'data_content': formatted_content})
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'}), 400

@app.route('/render', methods=['POST'])
def render():
    status = {
        'template_size': 0,
        'data_size': 0,
        'data_format': None,
        'parse_time_ms': 0,
        'render_time_ms': 0,
        'output_size': 0,
        'warnings': [],
    }
    try:
        template_str = request.form.get('template', '')
        data_str = request.form.get('data', '{}')
        # Get whitespace control preferences, default to True
        trim_blocks = request.form.get('trim_blocks', 'true').lower() == 'true'
        lstrip_blocks = request.form.get('lstrip_blocks', 'true').lower() == 'true'

        status['template_size'] = len(template_str.encode('utf-8'))
        status['data_size'] = len(data_str.encode('utf-8'))

        if status['data_size'] > 100 * 1024:
            status['warnings'].append(f"Large data input: {status['data_size'] / 1024:.1f} KB")

        # Try parsing as JSON first, then YAML
        parse_start = time.time()
        try:
            data = json.loads(data_str)
            status['data_format'] = 'json'
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(data_str)
                status['data_format'] = 'yaml'
            except yaml.YAMLError as e:
                status['parse_time_ms'] = round((time.time() - parse_start) * 1000)
                status['data_format'] = 'invalid'
                return jsonify({
                    'is_valid': False,
                    'result': f'Invalid data format: {str(e)}',
                    'rendered_output': None,
                    'status': status
                })
        status['parse_time_ms'] = round((time.time() - parse_start) * 1000)

        # Validate and render the template with whitespace control options
        render_start = time.time()
        is_valid, result = validate_template(template_str, trim_blocks, lstrip_blocks)
        if is_valid:
            success, rendered = render_template_string(template_str, data, trim_blocks, lstrip_blocks)
            status['render_time_ms'] = round((time.time() - render_start) * 1000)
            if success:
                status['output_size'] = len(rendered.encode('utf-8'))
                return jsonify({
                    'is_valid': True,
                    'result': 'Template is valid',
                    'rendered_output': rendered,
                    'status': status
                })
            else:
                return jsonify({
                    'is_valid': False,
                    'result': rendered,
                    'rendered_output': None,
                    'status': status
                })
        else:
            status['render_time_ms'] = round((time.time() - render_start) * 1000)
            return jsonify({
                'is_valid': False,
                'result': result,
                'rendered_output': None,
                'status': status
            })
    except Exception as e:
        return jsonify({
            'is_valid': False,
            'result': f'Error: {str(e)}',
            'rendered_output': None,
            'status': status
        })

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main() 