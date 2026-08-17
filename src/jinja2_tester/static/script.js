const jsYaml = document.createElement('script');
jsYaml.src = 'https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js';
document.head.appendChild(jsYaml);

document.addEventListener('DOMContentLoaded', function() {
    const templateInput = document.getElementById('templateInput');
    const dataInput = document.getElementById('dataInput');
    const validateBtn = document.getElementById('validateBtn');
    const uploadTemplateBtn = document.getElementById('uploadTemplateBtn');
    const uploadDataBtn = document.getElementById('uploadDataBtn');
    const templateFile = document.getElementById('templateFile');
    const dataFile = document.getElementById('dataFile');
    const resultDiv = document.getElementById('resultDiv');
    const outputArea = document.getElementById('outputArea');
    const dataFormatSelect = document.getElementById('dataFormatSelect');
    const formatDataBtn = document.getElementById('formatDataBtn');
    const statusBtn = document.getElementById('statusBtn');
    const statusPanel = document.getElementById('statusPanel');
    const statusCloseBtn = document.getElementById('statusCloseBtn');

    let debounceTimeout;
    let lastStatus = null;

    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        if (bytes < 1024) return bytes + ' B';
        return (bytes / 1024).toFixed(1) + ' KB';
    }

    function updateStatusPanel(status, errorMsg) {
        lastStatus = status;
        if (!status) {
            statusBtn.className = 'status-button';
            return;
        }

        document.getElementById('statusTemplateSize').textContent = formatBytes(status.template_size);
        document.getElementById('statusDataSize').textContent = formatBytes(status.data_size);
        document.getElementById('statusDataFormat').textContent = status.data_format || '--';
        document.getElementById('statusParseTime').textContent = status.parse_time_ms + ' ms';
        document.getElementById('statusRenderTime').textContent = status.render_time_ms + ' ms';
        document.getElementById('statusOutputSize').textContent = formatBytes(status.output_size);

        // Show warnings
        const warningsDiv = document.getElementById('statusWarnings');
        if (status.warnings && status.warnings.length > 0) {
            warningsDiv.innerHTML = status.warnings.map(w => '<div class="status-warning-item">Warning: ' + w + '</div>').join('');
            warningsDiv.style.display = 'block';
        } else {
            warningsDiv.style.display = 'none';
        }

        // Show error detail
        const errorDiv = document.getElementById('statusError');
        if (errorMsg) {
            errorDiv.textContent = errorMsg;
            errorDiv.style.display = 'block';
            statusBtn.className = 'status-button status-has-error';
        } else {
            errorDiv.style.display = 'none';
            if (status.warnings && status.warnings.length > 0) {
                statusBtn.className = 'status-button status-has-warning';
            } else {
                statusBtn.className = 'status-button status-ok';
            }
        }
    }

    // Function to update the rendered output
    function updateRenderedOutput() {
        // Show loading state
        outputArea.innerHTML = '<div class="placeholder-text">Rendering...</div>';
        outputArea.classList.add('empty');

        const formData = new FormData();
        formData.append('template', templateInput.value);
        formData.append('data', dataInput.value);
        // Add whitespace control preferences
        formData.append('trim_blocks', document.getElementById('trimBlocksToggle').checked);
        formData.append('lstrip_blocks', document.getElementById('lstripBlocksToggle').checked);

        fetch('/render', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Update result message
            resultDiv.textContent = data.result;
            resultDiv.className = `result ${data.is_valid ? 'success' : 'error'}`;
            resultDiv.style.display = 'block';

            // Update status panel
            updateStatusPanel(data.status, data.is_valid ? null : data.result);

            // Update rendered output
            if (data.rendered_output !== null) {
                outputArea.textContent = data.rendered_output;
                outputArea.classList.remove('empty');
            } else {
                outputArea.innerHTML = '<div class="placeholder-text">No output to display</div>';
                outputArea.classList.add('empty');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.textContent = 'Error: Failed to render template';
            resultDiv.className = 'result error';
            resultDiv.style.display = 'block';
            updateStatusPanel(null, 'Network error: ' + error.message);
            statusBtn.className = 'status-button status-has-error';
            outputArea.innerHTML = '<div class="placeholder-text">Error occurred while rendering</div>';
            outputArea.classList.add('empty');
        });
    }

    // Debounced input handler
    function debounceInput() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(updateRenderedOutput, 500); // 500ms delay
    }

    // Add input event listeners for real-time updates
    templateInput.addEventListener('input', debounceInput);
    dataInput.addEventListener('input', debounceInput);

    // Validate button click handler
    validateBtn.addEventListener('click', function(e) {
        e.preventDefault();
        updateRenderedOutput();
    });

    // File upload handlers
    uploadTemplateBtn.addEventListener('click', () => templateFile.click());
    uploadDataBtn.addEventListener('click', () => dataFile.click());

    templateFile.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('template_file', file);

            fetch('/upload-template', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    templateInput.value = data.template_content;
                    updateRenderedOutput(); // Trigger render after loading template
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to upload template file');
            });
        }
    });

    // Function to detect data format
    function detectDataFormat(content) {
        try {
            JSON.parse(content);
            return 'json';
        } catch (e) {
            try {
                jsYaml.load(content);
                return 'yaml';
            } catch (e) {
                return null;
            }
        }
    }

    // Function to format data
    function formatData(content, format) {
        try {
            let data;
            if (format === 'json') {
                // If input is YAML, convert to JSON
                try {
                    data = JSON.parse(content);
                } catch {
                    data = jsYaml.load(content);
                }
                return JSON.stringify(data, null, 2);
            } else {
                // If input is JSON, convert to YAML
                try {
                    data = JSON.parse(content);
                } catch {
                    data = jsYaml.load(content);
                }
                return jsYaml.dump(data, {
                    indent: 2,
                    lineWidth: -1,
                    noRefs: true,
                    sortKeys: true
                });
            }
        } catch (e) {
            throw new Error(`Invalid ${format.toUpperCase()} format: ${e.message}`);
        }
    }

    // Format button click handler
    formatDataBtn.addEventListener('click', function() {
        const content = dataInput.value.trim();
        if (!content) {
            alert('No data to format');
            return;
        }

        try {
            const formattedContent = formatData(content, dataFormatSelect.value);
            dataInput.value = formattedContent;
        } catch (e) {
            alert(e.message);
        }
    });

    // Data format change handler
    dataFormatSelect.addEventListener('change', function() {
        if (this.value === 'apstra') return;

        const content = dataInput.value.trim();
        if (!content) return;

        try {
            const formattedContent = formatData(content, this.value);
            dataInput.value = formattedContent;
        } catch (e) {
            alert(`Failed to convert to ${this.value.toUpperCase()}: ${e.message}`);
            // Revert selection
            this.value = this.value === 'json' ? 'yaml' : 'json';
        }
    });

    // Update file upload handler for data
    dataFile.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const extension = file.name.toLowerCase().split('.').pop();
            const format = extension === 'json' ? 'json' : 'yaml';
            
            const formData = new FormData();
            formData.append('data_file', file);

            fetch('/upload-data', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // Update format selector and data input
                    dataFormatSelect.value = format;
                    dataInput.value = data.data_content;
                    // Force a render update
                    updateRenderedOutput();
                    // Clear the file input
                    dataFile.value = '';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to upload data file');
            });
        }
    });

    // Update download data handler
    document.getElementById('downloadDataBtn').addEventListener('click', function() {
        let content = dataInput.value;
        if (content.trim()) {
            try {
                const format = dataFormatSelect.value;
                content = formatData(content, format);
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const extension = format === 'json' ? 'json' : 'yml';
                downloadFile(
                    content,
                    `data-${timestamp}.${extension}`,
                    format === 'json' ? 'application/json' : 'application/x-yaml'
                );
            } catch (e) {
                alert(`Invalid ${dataFormatSelect.value.toUpperCase()} data: ${e.message}`);
            }
        } else {
            alert('No data content to download');
        }
    });

    // Initial render if there's content
    if (templateInput.value || dataInput.value !== '{}') {
        updateRenderedOutput();
    }

    // Function to download content as file
    function downloadFile(content, filename, contentType = 'text/plain') {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    // Download template button handler
    document.getElementById('downloadTemplateBtn').addEventListener('click', function() {
        const content = templateInput.value;
        if (content.trim()) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            downloadFile(content, `template-${timestamp}.j2`);
        } else {
            alert('No template content to download');
        }
    });

    // Download output button handler
    document.getElementById('downloadOutputBtn').addEventListener('click', function() {
        const content = outputArea.textContent;
        if (content && !outputArea.classList.contains('empty')) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            downloadFile(content, `rendered-output-${timestamp}.txt`);
        } else {
            alert('No rendered output to download');
        }
    });

    // Add CSS styles for download button positioning
    const style = document.createElement('style');
    style.textContent = `
        .input-controls {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .secondary-button {
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .secondary-button:hover {
            background-color: #5a6268;
        }
    `;
    document.head.appendChild(style);

    // Status button toggle
    statusBtn.addEventListener('click', function() {
        statusPanel.style.display = statusPanel.style.display === 'none' ? 'block' : 'none';
    });
    statusCloseBtn.addEventListener('click', function() {
        statusPanel.style.display = 'none';
    });

    // Add event listeners for the checkboxes
    document.getElementById('trimBlocksToggle').addEventListener('change', debounceInput);
    document.getElementById('lstripBlocksToggle').addEventListener('change', debounceInput);

    // --- Apstra Device Context Modal and Logic ---
    const apstraModal = document.getElementById('apstraModal');
    const closeApstraModal = document.getElementById('closeApstraModal');
    const cancelApstraBtn = document.getElementById('cancelApstraBtn');
    const connectApstraBtn = document.getElementById('connectApstraBtn');
    const submitApstraBtn = document.getElementById('submitApstraBtn');

    // Toggles and inputs
    const toggleBpBtn = document.getElementById('toggleBlueprintInput');
    const bpSelect = document.getElementById('apstraBlueprintSelect');
    const bpDirect = document.getElementById('apstraBlueprintDirect');

    const toggleSvBtn = document.getElementById('toggleServerInput');
    const svSelect = document.getElementById('apstraServerSelect');
    const svDirect = document.getElementById('apstraServerDirect');

    // Load saved settings from localStorage
    function loadSavedApstraSettings() {
        const storedIp = localStorage.getItem('apstraIp');
        const storedPort = localStorage.getItem('apstraPort');
        const storedUsername = localStorage.getItem('apstraUsername');
        if (storedIp) document.getElementById('apstraIp').value = storedIp;
        if (storedPort) document.getElementById('apstraPort').value = storedPort;
        if (storedUsername) document.getElementById('apstraUsername').value = storedUsername;
    }

    // Save settings to localStorage
    function saveApstraSettings() {
        localStorage.setItem('apstraIp', document.getElementById('apstraIp').value.trim());
        localStorage.setItem('apstraPort', document.getElementById('apstraPort').value.trim());
        localStorage.setItem('apstraUsername', document.getElementById('apstraUsername').value.trim());
    }

    // Show modal when "apstra" is selected
    dataFormatSelect.addEventListener('change', function() {
        if (this.value === 'apstra') {
            loadSavedApstraSettings();
            apstraModal.style.display = 'flex';
        }
    });

    function hideModal() {
        apstraModal.style.display = 'none';
        dataFormatSelect.value = 'json'; // Reset select format to JSON
    }

    closeApstraModal.addEventListener('click', hideModal);
    cancelApstraBtn.addEventListener('click', hideModal);

    // Toggle manual vs list inputs
    toggleBpBtn.addEventListener('click', () => {
        if (bpSelect.style.display === 'none') {
            bpSelect.style.display = 'block';
            bpDirect.style.display = 'none';
        } else {
            bpSelect.style.display = 'none';
            bpDirect.style.display = 'block';
        }
    });

    toggleSvBtn.addEventListener('click', () => {
        if (svSelect.style.display === 'none') {
            svSelect.style.display = 'block';
            svDirect.style.display = 'none';
        } else {
            svSelect.style.display = 'none';
            svDirect.style.display = 'block';
        }
    });

    // Connect to Controller and Load Blueprints
    connectApstraBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const ip = document.getElementById('apstraIp').value.trim();
        const port = document.getElementById('apstraPort').value.trim();
        const username = document.getElementById('apstraUsername').value.trim();
        const password = document.getElementById('apstraPassword').value;

        if (!ip || !port || !username || !password) {
            alert('IP, Port, Username and Password are required to connect.');
            return;
        }

        saveApstraSettings();

        connectApstraBtn.textContent = 'Connecting...';
        connectApstraBtn.disabled = true;

        fetch('/apstra/blueprints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, port, username, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else if (data.blueprints && data.blueprints.length > 0) {
                // Populate Blueprint select and switch to dropdown mode
                bpSelect.innerHTML = data.blueprints.map(bp => `<option value="${bp.id}">${bp.label} (${bp.id})</option>`).join('');
                bpSelect.style.display = 'block';
                bpDirect.style.display = 'none';
                
                // Trigger loading systems for the first blueprint
                loadSystemsForBlueprint(bpSelect.value);
            } else {
                alert('No blueprints found on controller.');
            }
        })
        .catch(err => alert('Connection failed: ' + err.message))
        .finally(() => {
            connectApstraBtn.textContent = 'Connect & Load Choices';
            connectApstraBtn.disabled = false;
        });
    });

    // Load systems when blueprint selection changes
    bpSelect.addEventListener('change', function() {
        loadSystemsForBlueprint(this.value);
    });

    function loadSystemsForBlueprint(blueprint_id) {
        const ip = document.getElementById('apstraIp').value.trim();
        const port = document.getElementById('apstraPort').value.trim();
        const username = document.getElementById('apstraUsername').value.trim();
        const password = document.getElementById('apstraPassword').value;

        if (!blueprint_id) return;

        fetch('/apstra/systems', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, port, username, password, blueprint_id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.systems && data.systems.length > 0) {
                svSelect.innerHTML = data.systems.map(sys => `<option value="${sys.id}">${sys.label} (${sys.id})</option>`).join('');
                svSelect.style.display = 'block';
                svDirect.style.display = 'none';
            } else {
                svSelect.innerHTML = '<option value="">No systems found</option>';
                svSelect.style.display = 'block';
                svDirect.style.display = 'none';
            }
        })
        .catch(err => {
            console.error('Failed to load systems:', err);
        });
    }

    // Submit to fetch config-context
    submitApstraBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const ip = document.getElementById('apstraIp').value.trim();
        const port = document.getElementById('apstraPort').value.trim();
        const username = document.getElementById('apstraUsername').value.trim();
        const password = document.getElementById('apstraPassword').value;

        // Resolve blueprint_id & server_id based on whether dropdown or manual is visible
        const blueprint_id = bpSelect.style.display !== 'none' ? bpSelect.value : bpDirect.value.trim();
        const server_id = svSelect.style.display !== 'none' ? svSelect.value : svDirect.value.trim();

        if (!ip || !port || !blueprint_id || !server_id) {
            alert('IP, Port, Blueprint ID, and Server ID are all required to fetch.');
            return;
        }

        saveApstraSettings();

        submitApstraBtn.textContent = 'Fetching Context...';
        submitApstraBtn.disabled = true;

        fetch('/apstra/config-context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, port, username, password, blueprint_id, server_id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                // Populate the text editor with fetched context config
                dataInput.value = JSON.stringify(data.config_context, null, 2);
                dataFormatSelect.value = 'json'; // Switch selector format to JSON
                apstraModal.style.display = 'none';
                updateRenderedOutput(); // Render template
            }
        })
        .catch(err => alert('Fetch failed: ' + err.message))
        .finally(() => {
            submitApstraBtn.textContent = 'Fetch Context';
            submitApstraBtn.disabled = false;
        });
    });

    // --- Load Configlets into Template Select Dropdown ---
    const templateSelect = document.getElementById('templateSelect');

    function loadConfigletsList() {
        fetch('/apstra/configlets')
        .then(res => res.json())
        .then(data => {
            if (data.configlets) {
                data.configlets.forEach(filename => {
                    const opt = document.createElement('option');
                    opt.value = filename;
                    opt.textContent = filename;
                    templateSelect.appendChild(opt);
                });
            }
        })
        .catch(err => console.error('Failed to load configlets list:', err));
    }

    // Load list on startup
    loadConfigletsList();

    // Fetch template content on select change
    templateSelect.addEventListener('change', function() {
        const filename = this.value;
        if (!filename) return;

        fetch(`/apstra/configlet/${filename}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else if (data.content !== undefined) {
                templateInput.value = data.content;
                updateRenderedOutput(); // Render with the new template
            }
        })
        .catch(err => {
            console.error('Failed to load configlet content:', err);
            alert('Failed to load configlet content.');
        });
    });
}); 