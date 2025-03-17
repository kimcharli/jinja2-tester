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

    let debounceTimeout;

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

    // Add event listeners for the checkboxes
    document.getElementById('trimBlocksToggle').addEventListener('change', debounceInput);
    document.getElementById('lstripBlocksToggle').addEventListener('change', debounceInput);
}); 