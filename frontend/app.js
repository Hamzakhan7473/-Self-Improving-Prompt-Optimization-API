const API_BASE_URL = 'http://localhost:8000';

// General Purpose Templates
const PROMPT_TEMPLATES = {
    qa: {
        prompt_id: 'question_answering',
        template: `You are a helpful assistant. Answer the following question based on the context provided.

Context: {{context}}
Question: {{question}}

Instructions:
- Provide a clear, accurate answer based on the context
- If the answer is not in the context, say "I don't have enough information to answer this question"
- Be concise but complete
- Use the context to support your answer

Answer:`,
        schema: {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": "The answer to the question"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence score (0-1)"},
                "source": {"type": "string", "description": "Source of information if available"}
            },
            "required": ["answer"]
        }
    },
    summarization: {
        prompt_id: 'text_summarization',
        template: `You are an expert at summarizing text. Create a concise summary of the following text.

Text to summarize:
{{text}}

Requirements:
- Summarize the main points
- Keep it under {{max_length}} words
- Maintain key information
- Use clear, professional language

Summary:`,
        schema: {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "The summary of the text"},
                "word_count": {"type": "number", "description": "Number of words in the summary"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key points extracted"
                }
            },
            "required": ["summary"]
        }
    },
    classification: {
        prompt_id: 'text_classification',
        template: `You are a text classification expert. Classify the following text into one of the given categories.

Text: {{text}}
Categories: {{categories}}

Instructions:
- Analyze the text carefully
- Choose the most appropriate category
- Provide a confidence score
- Explain your reasoning briefly

Classification:`,
        schema: {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "The selected category"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence in classification"},
                "reasoning": {"type": "string", "description": "Brief explanation of the classification"}
            },
            "required": ["category", "confidence"]
        }
    },
    extraction: {
        prompt_id: 'data_extraction',
        template: `You are a data extraction specialist. Extract structured information from the following text.

Text: {{text}}
Fields to extract: {{fields}}

Instructions:
- Extract all requested fields
- If a field is not found, use null
- Maintain accuracy
- Preserve original values when possible

Extracted data:`,
        schema: {
            "type": "object",
            "properties": {
                "extracted_fields": {
                    "type": "object",
                    "description": "Object containing extracted field values"
                },
                "extraction_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "missing_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of fields that could not be extracted"
                }
            },
            "required": ["extracted_fields"]
        }
    }
};

// Example Test Cases
const EXAMPLE_TEST_CASES = {
    qa: `{"input": {"question": "What is the capital of France?", "context": "France is a country in Europe. Its capital city is Paris, known for the Eiffel Tower."}, "expected": "Paris"}
{"input": {"question": "What is 2+2?", "context": "Basic arithmetic: 2 plus 2 equals 4"}, "expected": "4"}
{"input": {"question": "Who wrote Romeo and Juliet?", "context": "William Shakespeare was an English playwright. He wrote many famous plays including Romeo and Juliet."}, "expected": "William Shakespeare"}`,
    summarization: `{"input": {"text": "Artificial intelligence is transforming industries across the globe. From healthcare to finance, AI applications are improving efficiency and enabling new capabilities. Machine learning algorithms can analyze vast amounts of data to identify patterns and make predictions. However, ethical considerations and bias in AI systems remain important challenges that need to be addressed.", "max_length": 30}, "expected": {"summary": "AI is transforming industries through machine learning, improving efficiency but facing ethical challenges.", "word_count": 15}}
{"input": {"text": "The company reported strong quarterly earnings, with revenue increasing by 25% year-over-year. The growth was driven by strong performance in the cloud services division. The CEO expressed optimism about future prospects.", "max_length": 25}, "expected": {"summary": "Company earnings up 25% YoY, driven by cloud services growth.", "word_count": 10}}`
};

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
        if (tabName === 'evaluate' || tabName === 'improve' || tabName === 'history') {
            loadPromptsForSelect();
        }
        if (tabName === 'history') {
            loadHistory();
        }
    });
});

// Template buttons
document.querySelectorAll('.template-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const template = PROMPT_TEMPLATES[btn.dataset.template];
        if (template) {
            document.getElementById('prompt-id').value = template.prompt_id;
            document.getElementById('prompt-template').value = template.template;
            document.getElementById('prompt-schema').value = JSON.stringify(template.schema, null, 2);
            showNotification(`Loaded ${btn.textContent} template`, 'success');
        }
    });
});

// Example buttons
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const example = EXAMPLE_TEST_CASES[btn.dataset.example];
        if (example) {
            document.getElementById('eval-test-cases').value = example;
            showNotification(`Loaded ${btn.textContent}`, 'success');
        }
    });
});

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// API helper
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
            mode: 'cors'
        };
        if (body) options.body = JSON.stringify(body);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
            throw new Error(errorData.detail || `Request failed: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            showNotification('Cannot connect to API. Make sure backend is running on http://localhost:8000', 'error');
        } else {
            showNotification(error.message, 'error');
        }
        throw error;
    }
}

// Load prompts for dropdowns
async function loadPromptsForSelect() {
    try {
        const prompts = await apiCall('/prompts/');
        const uniquePrompts = [...new Set(prompts.map(p => p.prompt_id))];
        
        const selects = ['eval-prompt-select', 'improve-prompt-select', 'history-prompt-select'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = selectId === 'history-prompt-select' 
                    ? '<option value="">All prompts...</option>'
                    : '<option value="">Select a prompt...</option>';
                uniquePrompts.forEach(promptId => {
                    const option = document.createElement('option');
                    option.value = promptId;
                    option.textContent = promptId;
                    select.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error('Error loading prompts:', error);
    }
}

// Create Prompt
document.getElementById('create-prompt-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultDiv = document.getElementById('create-result');
    resultDiv.innerHTML = '<div class="loading">Creating prompt...</div>';
    
    try {
        const promptData = {
            prompt_id: document.getElementById('prompt-id').value.trim(),
            template: document.getElementById('prompt-template').value.trim()
        };
        
        const schemaText = document.getElementById('prompt-schema').value.trim();
        if (schemaText) {
            promptData.schema_definition = JSON.parse(schemaText);
        }
        
        const result = await apiCall('/prompts/', 'POST', promptData);
        
        resultDiv.innerHTML = `
            <div class="success-box">
                <h3>
                    <svg class="success-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Prompt Created Successfully!
                </h3>
                <p><strong>Prompt ID:</strong> ${result.prompt_id}</p>
                <p><strong>Version:</strong> ${result.version}</p>
                <p><strong>Status:</strong> <span class="badge">${result.status}</span></p>
                <p style="margin-top: 1rem; color: var(--text-secondary);">
                    Your prompt is ready! Switch to "Evaluate" tab to test it.
                </p>
            </div>
        `;
        
        showNotification(`Prompt "${result.prompt_id}" created (v${result.version})`, 'success');
        e.target.reset();
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error-box">
                <svg class="error-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Error: ${error.message}
            </div>`;
    }
});

// Evaluate Prompt
document.getElementById('evaluate-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultDiv = document.getElementById('evaluate-result');
    resultDiv.innerHTML = '<div class="loading">Running evaluation...</div>';
    
    try {
        const promptId = document.getElementById('eval-prompt-select').value;
        const testCasesText = document.getElementById('eval-test-cases').value.trim();
        
        const testCases = testCasesText.split('\n')
            .filter(line => line.trim())
            .map(line => {
                const parsed = JSON.parse(line);
                return {
                    variables: parsed.input,
                    expected_output: parsed.expected
                };
            });
        
        const prompts = await apiCall(`/prompts/?prompt_id=${promptId}`);
        if (prompts.length === 0) {
            throw new Error('Prompt not found');
        }
        const latestPrompt = prompts[0];
        
        const evalRequest = {
            request: {
                prompt_version_id: latestPrompt.id,
                dataset_id: `eval_${Date.now()}`
            },
            dataset_data: {
                dataset_id: `eval_${Date.now()}`,
                cases: testCases.map((tc, idx) => ({
                    input: tc.variables,
                    expected_output: tc.expected_output
                }))
            }
        };
        
        const result = await apiCall('/evaluation/', 'POST', evalRequest);
        
        const scoresHtml = result.scores.map(score => `
            <div class="score-item">
                <span class="score-label">${score.dimension.replace('_', ' ').toUpperCase()}</span>
                <span class="score-value">${(score.score * 100).toFixed(1)}%</span>
            </div>
        `).join('');
        
        resultDiv.innerHTML = `
            <div class="result-box">
                <h3>
                    <svg class="result-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                    </svg>
                    Evaluation Results
                </h3>
                <div class="metrics-grid">
                    <div class="metric-card primary">
                        <div class="metric-label">Overall Score</div>
                        <div class="metric-value">${(result.aggregate_score * 100).toFixed(1)}%</div>
                    </div>
                    <div class="metric-card success">
                        <div class="metric-label">Passed Cases</div>
                        <div class="metric-value">${result.passed_cases} / ${result.total_cases}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Failed Cases</div>
                        <div class="metric-value">${result.failed_cases}</div>
                    </div>
                </div>
                <div class="scores-section">
                    <h4>Evaluation Dimensions:</h4>
                    ${scoresHtml}
                </div>
                <p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                    The system evaluated your prompt across multiple dimensions including correctness, format adherence, verbosity, safety, and consistency.
                </p>
            </div>
        `;
        
        showNotification('Evaluation completed!', 'success');
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error-box">
                <svg class="error-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Error: ${error.message}
            </div>`;
    }
});

// Auto-Improve Prompt
document.getElementById('improve-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultDiv = document.getElementById('improve-result');
    resultDiv.innerHTML = '<div class="loading">Analyzing failures and generating improvements...<br><small>This may take a few minutes</small></div>';
    
    try {
        const promptId = document.getElementById('improve-prompt-select').value;
        const testCasesText = document.getElementById('improve-test-cases').value.trim();
        const autoPromote = document.getElementById('auto-promote').checked;
        
        const testCases = testCasesText.split('\n')
            .filter(line => line.trim())
            .map(line => {
                const parsed = JSON.parse(line);
                return {
                    input: parsed.input,
                    expected_output: parsed.expected
                };
            });
        
        const prompts = await apiCall(`/prompts/?prompt_id=${promptId}`);
        if (prompts.length === 0) {
            throw new Error('Prompt not found');
        }
        const latestPrompt = prompts[0];
        
        const dataset = {
            dataset_id: `improve_${Date.now()}`,
            cases: testCases
        };
        
        const result = await apiCall(`/improvement/self-improve/${latestPrompt.id}`, 'POST', {
            dataset_data: dataset,
            auto_promote: autoPromote
        });
        
        let resultHtml = `
            <div class="result-box">
                <h3>
                    <svg class="result-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m15.364-6.364l-4.243 4.243M7.879 16.121l-4.243 4.243m12.728 0l-4.243-4.243M7.879 7.879L3.636 3.636"></path>
                    </svg>
                    Auto-Improvement Results
                </h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Candidates Generated</div>
                        <div class="metric-value">${result.candidates_generated || 0}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Experiments Run</div>
                        <div class="metric-value">${result.experiments?.length || 0}</div>
                    </div>
                </div>
        `;
        
        if (result.promoted_version_id) {
            resultHtml += `
                <div class="success-box" style="margin-top: 1rem;">
                    <h4>
                        <svg class="success-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        New Version Promoted!
                    </h4>
                    <p><strong>Version ID:</strong> ${result.promoted_version_id}</p>
                    <p><strong>Auto-Promoted:</strong> ${result.auto_promoted ? 'Yes' : 'No'}</p>
                    <p style="margin-top: 0.5rem; color: var(--text-secondary);">
                        The improved prompt met all improvement thresholds and was automatically promoted.
                    </p>
                </div>
            `;
        } else {
            resultHtml += `
                <div class="info-box" style="margin-top: 1rem;">
                    <p>No version was automatically promoted. Check the experiments below to see results and manually promote if needed.</p>
                </div>
            `;
        }
        
        if (result.experiments && result.experiments.length > 0) {
            resultHtml += `
                <div style="margin-top: 1.5rem;">
                    <h4>Experiments & A/B Test Results:</h4>
                    <pre style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.85rem;">${JSON.stringify(result.experiments, null, 2)}</pre>
                </div>
            `;
        }
        
        resultHtml += '</div>';
        resultDiv.innerHTML = resultHtml;
        
        showNotification('Auto-improvement completed!', 'success');
        loadPromptsForSelect();
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error-box">
                <svg class="error-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Error: ${error.message}
            </div>`;
    }
});

// Load History
async function loadHistory() {
    const contentDiv = document.getElementById('history-content');
    const promptId = document.getElementById('history-prompt-select').value;
    
    contentDiv.innerHTML = '<div class="loading">Loading prompt history...</div>';
    
    try {
        const url = promptId ? `/prompts/?prompt_id=${promptId}` : '/prompts/';
        const prompts = await apiCall(url);
        
        if (prompts.length === 0) {
            contentDiv.innerHTML = '<p>No prompts found. Create one to get started!</p>';
            return;
        }
        
        const grouped = {};
        prompts.forEach(p => {
            if (!grouped[p.prompt_id]) grouped[p.prompt_id] = [];
            grouped[p.prompt_id].push(p);
        });
        
        let html = '';
        Object.entries(grouped).forEach(([promptId, versions]) => {
            html += `
                <div class="history-group">
                    <h3>${promptId}</h3>
                    ${versions.map(v => `
                        <div class="version-card">
                            <div class="version-header">
                                <span class="version-badge">v${v.version}</span>
                                <span class="status-badge ${v.status}">${v.status}</span>
                                <span class="version-date">${new Date(v.created_at).toLocaleString()}</span>
                            </div>
                            <div class="version-content">
                                <p><strong>Template:</strong></p>
                                <pre class="template-preview">${v.template.substring(0, 300)}${v.template.length > 300 ? '...' : ''}</pre>
                                ${v.schema_definition ? `<p style="margin-top: 0.5rem;"><strong>Schema:</strong> Defined (${Object.keys(v.schema_definition.properties || {}).length} properties)</p>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        });
        
        contentDiv.innerHTML = html;
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="error-box">
                <svg class="error-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Error: ${error.message}
            </div>`;
    }
}

document.getElementById('history-prompt-select').addEventListener('change', loadHistory);

// Test connection on load
async function testConnection() {
    try {
        await apiCall('/health');
        console.log('API connected');
        loadPromptsForSelect();
    } catch (error) {
        console.error('API connection failed:', error);
        showNotification('Cannot connect to API server. Make sure backend is running.', 'error');
    }
}

testConnection();
