from flask import Flask, render_template, request, jsonify
from jinja2 import Environment, meta, exceptions
import json
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

ALLOWED_TEMPLATE_EXTENSIONS = {'.j2', '.jinja', '.jinja2', '.html', '.txt'}
ALLOWED_DATA_EXTENSIONS = {'.json', '.yaml', '.yml', '.csv'}

def is_allowed_template_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_TEMPLATE_EXTENSIONS

def is_allowed_data_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_DATA_EXTENSIONS

def validate_template(template_str):
    try:
        env = Environment()
        env.parse(template_str)
        return True, "Template syntax is valid"
    except exceptions.TemplateSyntaxError as e:
        return False, f"Template syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error validating template: {str(e)}"

def render_template_string(template_str, data):
    try:
        env = Environment()
        template = env.from_string(template_str)
        return True, template.render(**data)
    except Exception as e:
        return False, f"Error rendering template: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        template_input = request.form.get('template', '')
        data_input = request.form.get('data', '{}')
        
        # Validate template
        is_valid, result = validate_template(template_input)
        
        if is_valid:
            try:
                # Parse data
                data = json.loads(data_input)
                
                # Render template
                success, rendered = render_template_string(template_input, data)
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
            except json.JSONDecodeError as e:
                return render_template('index.html',
                                     template_input=template_input,
                                     data_input=data_input,
                                     is_valid=False,
                                     result=f"Invalid JSON data: {str(e)}")
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
        elif ext in {'.yaml', '.yml'}:
            data = yaml.safe_load(content)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        return jsonify({'data_content': json.dumps(data, indent=2)})
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'}), 400

@app.route('/render', methods=['POST'])
def render():
    try:
        template_str = request.form.get('template', '')
        data_str = request.form.get('data', '{}')
        
        # Parse the JSON data
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            return jsonify({
                'is_valid': False,
                'result': f'Invalid JSON data: {str(e)}',
                'rendered_output': None
            })

        # Validate and render the template
        is_valid, result = validate_template(template_str)
        if is_valid:
            success, rendered = render_template_string(template_str, data)
            if success:
                return jsonify({
                    'is_valid': True,
                    'result': 'Template is valid',
                    'rendered_output': rendered
                })
            else:
                return jsonify({
                    'is_valid': False,
                    'result': rendered,
                    'rendered_output': None
                })
        else:
            return jsonify({
                'is_valid': False,
                'result': result,
                'rendered_output': None
            })
    except Exception as e:
        return jsonify({
            'is_valid': False,
            'result': f'Error: {str(e)}',
            'rendered_output': None
        })

if __name__ == '__main__':
    app.run(debug=True) 