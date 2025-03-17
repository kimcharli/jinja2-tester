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

    let debounceTimeout;

    // Function to update the rendered output
    function updateRenderedOutput() {
        // Show loading state
        outputArea.innerHTML = '<div class="placeholder-text">Rendering...</div>';
        outputArea.classList.add('empty');
        
        const formData = new FormData();
        formData.append('template', templateInput.value);
        formData.append('data', dataInput.value || '{}');

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

    dataFile.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
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
                    dataInput.value = data.data_content;
                    updateRenderedOutput(); // Trigger render after loading data
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to upload data file');
            });
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

    // Download data button handler
    document.getElementById('downloadDataBtn').addEventListener('click', function() {
        let content = dataInput.value;
        if (content.trim()) {
            try {
                // Try to format JSON if it's valid
                const jsonData = JSON.parse(content);
                content = JSON.stringify(jsonData, null, 2);
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                downloadFile(content, `data-${timestamp}.json`, 'application/json');
            } catch (e) {
                alert('Invalid JSON data');
            }
        } else {
            alert('No data content to download');
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
}); 