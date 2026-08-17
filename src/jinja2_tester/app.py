import json
import os
import socket
import time

import requests
import urllib3
import yaml
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from jinja2 import Environment, exceptions

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max file size
app.request_class.max_form_memory_size = 5 * 1024 * 1024  # 5MB max form field size
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")

ALLOWED_TEMPLATE_EXTENSIONS = {".j2", ".jinja", ".jinja2", ".html", ".txt"}
ALLOWED_DATA_EXTENSIONS = {".json", ".yaml", ".yml", ".csv"}


def is_allowed_template_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_TEMPLATE_EXTENSIONS


def is_allowed_data_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_DATA_EXTENSIONS


def jinja_contains(value, item):
    """Custom Jinja2 test to check if value contains item."""
    if value is None:
        return False
    try:
        return item in value
    except TypeError:
        return False


def validate_template(template_str, trim_blocks=True, lstrip_blocks=True):
    try:
        env = Environment(
            trim_blocks=trim_blocks,  # Removes first newline after a block
            # Strips leading whitespace before block tags
            lstrip_blocks=lstrip_blocks,
            extensions=["jinja2.ext.do"],
        )
        env.tests["contains"] = jinja_contains
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
            extensions=["jinja2.ext.do"],
        )
        env.tests["contains"] = jinja_contains
        template = env.from_string(template_str)
        return True, template.render(**data)
    except Exception as e:
        return False, f"Error rendering template: {str(e)}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        template_input = request.form.get("template", "")
        data_input = request.form.get("data", "{}")
        trim_blocks = request.form.get("trim_blocks", "true").lower() == "true"
        lstrip_blocks = request.form.get("lstrip_blocks", "true").lower() == "true"

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
                        return render_template(
                            "index.html",
                            template_input=template_input,
                            data_input=data_input,
                            is_valid=False,
                            result=f"Invalid data format: {str(e)}",
                        )

                # Render template
                success, rendered = render_template_string(
                    template_input, data, trim_blocks, lstrip_blocks
                )
                if success:
                    return render_template(
                        "index.html",
                        template_input=template_input,
                        data_input=data_input,
                        is_valid=True,
                        result="Template is valid",
                        rendered_output=rendered,
                    )
                else:
                    return render_template(
                        "index.html",
                        template_input=template_input,
                        data_input=data_input,
                        is_valid=False,
                        result=rendered,
                    )
            except Exception as e:
                return render_template(
                    "index.html",
                    template_input=template_input,
                    data_input=data_input,
                    is_valid=False,
                    result=f"Error: {str(e)}",
                )
        else:
            return render_template(
                "index.html",
                template_input=template_input,
                data_input=data_input,
                is_valid=False,
                result=result,
            )

    return render_template(
        "index.html", template_input="", data_input="{}", is_valid=None, result=None
    )


@app.route("/upload-template", methods=["POST"])
def upload_template():
    if "template_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["template_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not is_allowed_template_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        template_content = file.read().decode("utf-8")
        return jsonify({"template_content": template_content})
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 400


@app.route("/upload-data", methods=["POST"])
def upload_data():
    if "data_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["data_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not is_allowed_data_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        content = file.read().decode("utf-8")
        ext = os.path.splitext(file.filename)[1].lower()

        if ext in {".json"}:
            data = json.loads(content)
            formatted_content = json.dumps(data, indent=2)
        elif ext in {".yaml", ".yml"}:
            data = yaml.safe_load(content)
            formatted_content = yaml.dump(
                data, default_flow_style=False, sort_keys=True
            )
        else:
            return jsonify({"error": "Unsupported file format"}), 400

        return jsonify({"data_content": formatted_content})
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 400


@app.route("/render", methods=["POST"])
def render():
    status = {
        "template_size": 0,
        "data_size": 0,
        "data_format": None,
        "parse_time_ms": 0,
        "render_time_ms": 0,
        "output_size": 0,
        "warnings": [],
    }
    try:
        template_str = request.form.get("template", "")
        data_str = request.form.get("data", "{}")
        # Get whitespace control preferences, default to True
        trim_blocks = request.form.get("trim_blocks", "true").lower() == "true"
        lstrip_blocks = request.form.get("lstrip_blocks", "true").lower() == "true"

        status["template_size"] = len(template_str.encode("utf-8"))
        status["data_size"] = len(data_str.encode("utf-8"))

        if status["data_size"] > 100 * 1024:
            status["warnings"].append(
                f"Large data input: {status['data_size'] / 1024:.1f} KB"
            )

        # Try parsing as JSON first, then YAML
        parse_start = time.time()
        try:
            data = json.loads(data_str)
            status["data_format"] = "json"
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(data_str)
                status["data_format"] = "yaml"
            except yaml.YAMLError as e:
                status["parse_time_ms"] = round((time.time() - parse_start) * 1000)
                status["data_format"] = "invalid"
                return jsonify(
                    {
                        "is_valid": False,
                        "result": f"Invalid data format: {str(e)}",
                        "rendered_output": None,
                        "status": status,
                    }
                )
        status["parse_time_ms"] = round((time.time() - parse_start) * 1000)

        # Validate and render the template with whitespace control options
        render_start = time.time()
        is_valid, result = validate_template(template_str, trim_blocks, lstrip_blocks)
        if is_valid:
            success, rendered = render_template_string(
                template_str, data, trim_blocks, lstrip_blocks
            )
            status["render_time_ms"] = round((time.time() - render_start) * 1000)
            if success:
                status["output_size"] = len(rendered.encode("utf-8"))
                return jsonify(
                    {
                        "is_valid": True,
                        "result": "Template is valid",
                        "rendered_output": rendered,
                        "status": status,
                    }
                )
            else:
                return jsonify(
                    {
                        "is_valid": False,
                        "result": rendered,
                        "rendered_output": None,
                        "status": status,
                    }
                )
        else:
            status["render_time_ms"] = round((time.time() - render_start) * 1000)
            return jsonify(
                {
                    "is_valid": False,
                    "result": result,
                    "rendered_output": None,
                    "status": status,
                }
            )
    except Exception as e:
        return jsonify(
            {
                "is_valid": False,
                "result": f"Error: {str(e)}",
                "rendered_output": None,
                "status": status,
            }
        )


def get_apstra_session(ip, port, username, password):
    """Helper to authenticate and return an active requests Session."""
    session = requests.Session()
    session.verify = False  # Support self-signed certs
    url = f"https://{ip}:{port}"

    # Try the standard /api/aaa/login endpoint first, fallback to /api/user/login
    login_url = f"{url}/api/aaa/login"
    try:
        login_res = session.post(
            login_url,
            json={"username": username, "password": password},
            timeout=8,
        )
        login_res.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (404, 405):
            fallback_url = f"{url}/api/user/login"
            login_res = session.post(
                fallback_url,
                json={"username": username, "password": password},
                timeout=8,
            )
            login_res.raise_for_status()
        else:
            raise

    # Extract the token
    token_data = login_res.json()
    token = (
        token_data.get("token")
        or token_data.get("authtoken")
        or token_data.get("auth_token")
    )
    if token:
        session.headers.update({"AuthToken": token, "Authorization": f"Bearer {token}"})

    return session, url


@app.route("/apstra/blueprints", methods=["POST"])
def apstra_blueprints():
    data = request.json or {}
    try:
        session, url = get_apstra_session(
            data["ip"], data["port"], data["username"], data["password"]
        )
        res = session.get(f"{url}/api/blueprints", timeout=8)
        res.raise_for_status()

        blueprints_data = res.json()
        blueprints = []

        if isinstance(blueprints_data, list):
            for bp in blueprints_data:
                if isinstance(bp, dict):
                    bp_id = bp.get("id")
                    if bp_id:
                        blueprints.append(
                            {"id": bp_id, "label": bp.get("label") or bp_id}
                        )
        elif isinstance(blueprints_data, dict):
            if "items" in blueprints_data and isinstance(
                blueprints_data["items"], list
            ):
                for bp in blueprints_data["items"]:
                    if isinstance(bp, dict):
                        bp_id = bp.get("id")
                        if bp_id:
                            blueprints.append(
                                {"id": bp_id, "label": bp.get("label") or bp_id}
                            )
            else:
                for bp_id, bp_val in blueprints_data.items():
                    if isinstance(bp_val, dict):
                        blueprints.append(
                            {
                                "id": bp_id,
                                "label": bp_val.get("label") or bp_id,
                            }
                        )
                    elif isinstance(bp_val, str):
                        blueprints.append({"id": bp_id, "label": bp_val})

        return jsonify({"blueprints": blueprints})
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve blueprints: {str(e)}"}), 500


@app.route("/apstra/systems", methods=["POST"])
def apstra_systems():
    data = request.json or {}
    try:
        session, url = get_apstra_session(
            data["ip"], data["port"], data["username"], data["password"]
        )
        res = session.get(
            f"{url}/api/blueprints/{data['blueprint_id']}/systems", timeout=8
        )
        res.raise_for_status()

        systems_data = res.json()
        systems = []

        if isinstance(systems_data, list):
            for sys_item in systems_data:
                if isinstance(sys_item, dict):
                    sys_id = sys_item.get("id") or sys_item.get("system_id")
                    label = sys_item.get("hostname") or sys_item.get("label") or sys_id
                    if sys_id:
                        systems.append({"id": sys_id, "label": label})
        elif isinstance(systems_data, dict):
            if "items" in systems_data and isinstance(systems_data["items"], list):
                for sys_item in systems_data["items"]:
                    if isinstance(sys_item, dict):
                        sys_id = sys_item.get("id") or sys_item.get("system_id")
                        label = (
                            sys_item.get("hostname") or sys_item.get("label") or sys_id
                        )
                        if sys_id:
                            systems.append({"id": sys_id, "label": label})
            else:
                for sys_id, sys_val in systems_data.items():
                    if isinstance(sys_val, dict):
                        label = (
                            sys_val.get("hostname") or sys_val.get("label") or sys_id
                        )
                        systems.append({"id": sys_id, "label": label})
                    elif isinstance(sys_val, str):
                        systems.append({"id": sys_id, "label": sys_val})

        return jsonify({"systems": systems})
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve systems: {str(e)}"}), 500


@app.route("/apstra/config-context", methods=["POST"])
def apstra_config_context():
    data = request.json or {}
    try:
        session, url = get_apstra_session(
            data["ip"], data["port"], data["username"], data["password"]
        )
        bp_id = data["blueprint_id"]
        srv_id = data["server_id"]
        endpoint = f"{url}/api/blueprints/{bp_id}/systems/{srv_id}/config-context"
        res = session.get(endpoint, timeout=10)
        res.raise_for_status()

        res_data = res.json()
        context_data = res_data

        # Resolve/unwrap "context" if nested in the response
        if isinstance(res_data, dict):
            inner_context = (
                res_data.get("context")
                or res_data.get("config_context")
                or res_data.get("config-context")
            )
            if inner_context is not None:
                if isinstance(inner_context, dict):
                    context_data = inner_context
                elif isinstance(inner_context, str):
                    try:
                        context_data = json.loads(inner_context)
                    except json.JSONDecodeError:
                        # Fallback if string is not valid JSON
                        context_data = {"context": inner_context}

        return jsonify({"config_context": context_data})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch config context: {str(e)}"}), 500


@app.route("/apstra/configlets", methods=["GET"])
def apstra_configlets():
    try:
        # Resolve configlets directory path relative to app root
        configlets_dir = os.path.abspath(
            os.path.join(app.root_path, "..", "..", "apstra_configlets")
        )
        if not os.path.isdir(configlets_dir):
            return jsonify({"error": "Configlets directory not found"}), 404

        # List all .j2 files, ignoring files starting with metadata prefix "_"
        files = sorted(
            [
                f
                for f in os.listdir(configlets_dir)
                if f.endswith(".j2") and not f.startswith("_")
            ]
        )
        return jsonify({"configlets": files})
    except Exception as e:
        return jsonify({"error": f"Failed to list configlets: {str(e)}"}), 500


@app.route("/apstra/configlet/<filename>", methods=["GET"])
def apstra_configlet_content(filename):
    try:
        # Sanitize filename to prevent directory traversal
        filename = os.path.basename(filename)
        configlets_dir = os.path.abspath(
            os.path.join(app.root_path, "..", "..", "apstra_configlets")
        )
        filepath = os.path.join(configlets_dir, filename)

        if not os.path.isfile(filepath):
            return jsonify({"error": "Configlet file not found"}), 404

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": f"Failed to read configlet: {str(e)}"}), 500


DEFAULT_PORT = 5001
PORT_SCAN_RANGE = 10


def find_available_port(start_port, scan_range=PORT_SCAN_RANGE):
    """Try start_port, then the next scan_range ports. Return first available."""
    for port in range(start_port, start_port + scan_range + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return None


def main():
    # If the port was already chosen by the parent process, reuse it
    # to prevent Flask's reloader subprocess from scanning and clashing
    env_port = os.getenv("JINJA2_TESTER_PORT")
    if env_port:
        app.run(debug=True, port=int(env_port))
        return

    port = int(os.getenv("PORT", DEFAULT_PORT))
    available = find_available_port(port)
    if available is None:
        end = port + PORT_SCAN_RANGE
        print(f"Error: No available port found in range {port}-{end}")
        return
    if available != port:
        print(f"Port {port} is in use, using port {available} instead")

    os.environ["JINJA2_TESTER_PORT"] = str(available)
    app.run(debug=True, port=available)


if __name__ == "__main__":
    main()
