const API_BASE = 'http://127.0.0.1:8001/api';

document.getElementById('load-workflows-btn').addEventListener('click', loadWorkflows);
document.getElementById('workflow-select').addEventListener('change', onWorkflowSelect);
document.getElementById('execute-btn').addEventListener('click', executeWorkflow);

async function loadWorkflows() {
    try {
        const res = await fetch(`${API_BASE}/workflows`);
        const workflows = await res.json();
        
        const select = document.getElementById('workflow-select');
        select.innerHTML = '<option value="">-- Select --</option>';
        
        workflows.forEach(wf => {
            const opt = document.createElement('option');
            opt.value = wf.id;
            opt.textContent = `${wf.name} (ID: ${wf.id})`;
            select.appendChild(opt);
        });
    } catch (e) {
        alert('Failed to load workflows. Is the backend running?');
        console.error(e);
    }
}

async function onWorkflowSelect(e) {
    const wfId = e.target.value;
    const container = document.getElementById('steps-container');
    const startStepInput = document.getElementById('start-step-id');
    
    if (!wfId) {
        container.innerHTML = '<p>Select a workflow to view steps.</p>';
        return;
    }
    
    try {
        container.innerHTML = 'Loading...';
        
        const res = await fetch(`${API_BASE}/workflows/${wfId}/steps`);
        const steps = await res.json();
        
        container.innerHTML = '';
        if (steps.length === 0) {
            container.innerHTML = '<p>No steps found.</p>';
            return;
        }
        
        // Auto-fill start step
        startStepInput.value = steps[0].id;
        
        steps.forEach(step => {
            const card = document.createElement('div');
            card.className = 'step-card';
            
            let rulesHtml = '';
            if (step.rules && step.rules.length > 0) {
                // sort rules by priority descending just for display
                const sortedRules = [...step.rules].sort((a,b)=>b.priority - a.priority);
                rulesHtml = '<ul class="rule-list">';
                sortedRules.forEach(r => {
                    rulesHtml += `
                        <li class="rule-item">
                            <span>If <span class="rule-condition">${r.condition}</span> (Priority: ${r.priority})</span>
                            <span>→ Goto Step ${r.next_step_id || 'End'}</span>
                        </li>
                    `;
                });
                rulesHtml += '</ul>';
            } else {
                rulesHtml = '<p style="font-size:0.9rem; color:#6B7280; margin:0;">No rules (End step)</p>';
            }
            
            card.innerHTML = `
                <h3>[ID: ${step.id}] ${step.name} (${step.step_type})</h3>
                ${rulesHtml}
            `;
            container.appendChild(card);
        });
        
    } catch (e) {
        container.innerHTML = '<p style="color:red;">Error loading steps</p>';
        console.error(e);
    }
}

async function executeWorkflow() {
    const wfId = document.getElementById('workflow-select').value;
    const startStepId = document.getElementById('start-step-id').value;
    const dataStr = document.getElementById('execution-data').value;
    const resultDiv = document.getElementById('execution-result');
    
    if (!wfId || !startStepId) {
        alert('Please select a workflow and valid start step ID');
        return;
    }
    
    let data;
    try {
        data = JSON.parse(dataStr);
    } catch (e) {
        alert('Invalid JSON in context data');
        return;
    }
    
    try {
        resultDiv.innerHTML = '<p>Executing...</p>';
        
        const res = await fetch(`${API_BASE}/workflows/${wfId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_step_id: parseInt(startStepId),
                data: data
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Execution failed');
        }
        
        const execution = await res.json();
        renderExecutionLogs(execution, resultDiv);
        
    } catch (e) {
        resultDiv.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
        console.error(e);
    }
}

function renderExecutionLogs(execution, container) {
    let html = `<h3>Final Status: <span style="color: ${execution.status === 'completed' ? 'var(--success)' : 'var(--error)'}">${execution.status.toUpperCase()}</span></h3>`;
    
    if (execution.logs && execution.logs.length > 0) {
        execution.logs.forEach((log, index) => {
            const isError = log.status.includes('error');
            const cssClass = isError ? 'error' : 'success';
            
            let evRulesHtml = '';
            if (log.evaluated_rules && log.evaluated_rules.length > 0) {
                evRulesHtml = '<ul>';
                log.evaluated_rules.forEach(r => {
                    const resStr = r.result ? '✅ (Matched)' : '❌';
                    evRulesHtml += `<li><span class="rule-condition">${r.condition}</span>: ${resStr}</li>`;
                });
                evRulesHtml += '</ul>';
            }
            
            html += `
                <div class="log-entry ${cssClass}">
                    <div class="log-header">
                        <span>Step ${index + 1}: ${log.step_name}</span>
                        <span>→ ${log.next_step ? 'Next Step ID: ' + log.next_step : 'End of Workflow'}</span>
                    </div>
                    <div class="log-details">
                        <strong>Rule Evaluation:</strong>
                        ${evRulesHtml || '<p style="margin:5px 0;">No rules evaluated (End Step)</p>'}
                    </div>
                </div>
            `;
        });
    } else {
        html += '<p>No logs found.</p>';
    }
    
    container.innerHTML = html;
}
