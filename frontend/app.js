const API_BASE_URL = 'http://localhost:8000';

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
    });
});

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// API helper
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            mode: 'cors', // Explicitly enable CORS
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        // Check if response is ok
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
            throw new Error(errorData.detail || `Request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        // More detailed error messages
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            showNotification('Cannot connect to API server. Make sure backend is running on http://localhost:8000', 'error');
        } else {
            showNotification(error.message, 'error');
        }
        console.error('API Error:', error);
        throw error;
    }
}

// Create Prompt
document.getElementById('create-prompt-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const promptData = {
            prompt_id: document.getElementById('prompt-id').value,
            template: document.getElementById('prompt-template').value,
        };
        
        // Parse optional fields
        const schemaText = document.getElementById('prompt-schema').value.trim();
        if (schemaText) {
            promptData.schema_definition = JSON.parse(schemaText);
        }
        
        const metadataText = document.getElementById('prompt-metadata').value.trim();
        if (metadataText) {
            promptData.metadata = JSON.parse(metadataText);
        }
        
        const result = await apiCall('/prompts/', 'POST', promptData);
        showNotification(`Prompt created: ${result.version}`, 'success');
        
        // Clear form
        e.target.reset();
        loadPrompts();
    } catch (error) {
        console.error('Error creating prompt:', error);
    }
});

// Load Prompts
async function loadPrompts() {
    const listDiv = document.getElementById('prompts-list');
    listDiv.innerHTML = '<div class="loading">Loading prompts</div>';
    
    try {
        const prompts = await apiCall('/prompts/');
        
        if (prompts.length === 0) {
            listDiv.innerHTML = '<p>No prompts found. Create one to get started!</p>';
            return;
        }
        
        listDiv.innerHTML = prompts.map(prompt => {
            const statusClass = prompt.status === 'active' ? 'status-active' : 
                               prompt.status === 'draft' ? 'status-draft' : 
                               'status-experimental';
            return `
            <div class="prompt-item">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <h4>${prompt.prompt_id} <span style="color: var(--text-secondary); font-weight: 400;">v${prompt.version}</span></h4>
                    <span class="status-badge ${statusClass}">${prompt.status}</span>
                </div>
                <p><strong>Created:</strong> ${new Date(prompt.created_at).toLocaleString()}</p>
                <p style="margin-top: 0.5rem; color: var(--text-secondary);"><strong>Template:</strong> ${prompt.template.substring(0, 120)}${prompt.template.length > 120 ? '...' : ''}</p>
            </div>
        `;
        }).join('');
    } catch (error) {
        listDiv.innerHTML = `<p style="color: red;">Error loading prompts: ${error.message}</p>`;
    }
}

// Run Inference
document.getElementById('inference-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultDiv = document.getElementById('inference-result');
    resultDiv.innerHTML = '<div class="loading">Running inference</div>';
    
    try {
        const requestData = {
            prompt_id: document.getElementById('inference-prompt-id').value,
            variables: JSON.parse(document.getElementById('inference-variables').value),
        };
        
        const version = document.getElementById('inference-version').value.trim();
        if (version) {
            requestData.version = version;
        }
        
        const result = await apiCall('/inference/', 'POST', requestData);
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h4>Inference Result</h4>
                <div style="margin-bottom: 1rem;">
                    <span class="status-badge status-active">Version ${result.version}</span>
                </div>
                <div style="margin-bottom: 1rem;">
                    <p style="color: var(--text-secondary); margin-bottom: 0.5rem; font-size: 0.875rem;">Output:</p>
                    <pre>${result.output}</pre>
                </div>
                ${result.metadata ? `<div style="margin-top: 1rem;"><p style="color: var(--text-secondary); margin-bottom: 0.5rem; font-size: 0.875rem;">Metadata:</p><pre>${JSON.stringify(result.metadata, null, 2)}</pre></div>` : ''}
            </div>
        `;
        
        showNotification('Inference completed', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// Run Evaluation
document.getElementById('evaluation-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultDiv = document.getElementById('evaluation-result');
    resultDiv.innerHTML = '<div class="loading">Running evaluation</div>';
    
    try {
        const dataset = JSON.parse(document.getElementById('eval-dataset').value);
        const requestData = {
            request: {
                prompt_version_id: parseInt(document.getElementById('eval-version-id').value),
                dataset_id: dataset.dataset_id,
            },
            dataset_data: dataset,
        };
        
        const result = await apiCall('/evaluation/', 'POST', requestData);
        
        const scoresHtml = result.scores.map(score => `
            <div class="metric-item">
                <span class="metric-label">${score.dimension}</span>
                <span class="metric-value">${(score.score * 100).toFixed(1)}%</span>
            </div>
        `).join('');
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h4>Evaluation Results</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0;">
                    <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid var(--glass-border);">
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">Aggregate Score</p>
                        <p style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${(result.aggregate_score * 100).toFixed(1)}%</p>
                    </div>
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid var(--glass-border);">
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">Pass Rate</p>
                        <p style="font-size: 1.5rem; font-weight: 700; color: var(--success);">${result.passed_cases} / ${result.total_cases}</p>
                    </div>
                </div>
                <div style="margin-top: 1.5rem;">
                    <h5 style="margin-bottom: 1rem; color: var(--text-primary);">Dimension Scores</h5>
                    ${scoresHtml}
                </div>
            </div>
        `;
        
        showNotification('Evaluation completed', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// Run Self-Improvement
document.getElementById('improvement-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultDiv = document.getElementById('improvement-result');
    resultDiv.innerHTML = '<div class="loading">Running self-improvement (this may take a while)</div>';
    
    try {
        const dataset = JSON.parse(document.getElementById('improve-dataset').value);
        const versionId = parseInt(document.getElementById('improve-version-id').value);
        const autoPromote = document.getElementById('auto-promote').checked;
        
        const result = await apiCall(`/improvement/self-improve/${versionId}`, 'POST', {
            dataset_data: dataset,
            auto_promote: autoPromote,
        });
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h4>Self-Improvement Results</h4>
                <p><strong>Candidates Generated:</strong> ${result.candidates_generated}</p>
                <p><strong>Experiments Run:</strong> ${result.experiments.length}</p>
                ${result.promoted_version_id ? `<p><strong>Promoted Version ID:</strong> ${result.promoted_version_id}</p>` : ''}
                <p><strong>Auto-Promoted:</strong> ${result.auto_promoted ? 'Yes' : 'No'}</p>
                <div style="margin-top: 15px;">
                    <h5>Experiments:</h5>
                    <pre>${JSON.stringify(result.experiments, null, 2)}</pre>
                </div>
            </div>
        `;
        
        showNotification('Self-improvement completed', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// A/B Testing - Select Version
document.getElementById('ab-select-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultDiv = document.getElementById('ab-select-result');
    resultDiv.innerHTML = '<div class="loading">Selecting version</div>';
    
    try {
        const promptId = document.getElementById('ab-prompt-id').value;
        const userId = document.getElementById('ab-user-id').value.trim();
        
        const url = `/ab-testing/select/${promptId}${userId ? `?user_id=${userId}` : ''}`;
        const result = await apiCall(url);
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h4>Selected Version</h4>
                <p><strong>Version ID:</strong> ${result.selected_version_id}</p>
                <p><strong>Version:</strong> ${result.selected_version}</p>
                <p><strong>Is Canary:</strong> ${result.is_canary ? 'Yes' : 'No'}</p>
                ${result.test_id ? `<p><strong>Test ID:</strong> ${result.test_id}</p>` : ''}
            </div>
        `;
        
        showNotification('Version selected', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// A/B Testing - Get Metrics
document.getElementById('ab-metrics-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultDiv = document.getElementById('ab-metrics-result');
    resultDiv.innerHTML = '<div class="loading">Loading metrics</div>';
    
    try {
        const promptId = document.getElementById('ab-metrics-prompt-id').value;
        const metrics = await apiCall(`/ab-testing/metrics/${promptId}`);
        
        const metricsHtml = metrics.metrics.map(metric => {
            const statusClass = metric.status === 'active' ? 'status-active' : 
                               metric.status === 'draft' ? 'status-draft' : 
                               'status-experimental';
            return `
            <div class="prompt-item">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <h4>Version ${metric.version} ${metric.is_active ? '<span style="color: var(--success);">● Active</span>' : ''}</h4>
                    <span class="status-badge ${statusClass}">${metric.status}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">Score</p>
                        <p style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">${(metric.aggregate_score * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">Created</p>
                        <p style="font-size: 0.875rem; color: var(--text-primary);">${new Date(metric.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
            </div>
        `;
        }).join('');
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h4>A/B Test Metrics for ${metrics.prompt_id}</h4>
                ${metricsHtml}
            </div>
        `;
        
        showNotification('Metrics loaded', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

// Test API connection on page load
async function testConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors'
        });
        if (response.ok) {
            console.log('✓ API connection successful');
            loadPrompts();
        } else {
            showNotification('API server returned an error. Check if backend is running.', 'error');
        }
    } catch (error) {
        console.error('✗ API connection failed:', error);
        showNotification('Cannot connect to API server at http://localhost:8000. Make sure the backend is running.', 'error');
    }
}

// Test connection and load prompts on page load
testConnection();

