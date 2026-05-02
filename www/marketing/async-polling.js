const asyncAggregateId = '<?= htmlspecialchars($result['aggregate_id']) ?>';
const asyncRepoUrl = '<?= htmlspecialchars($result['repo']) ?>';
let pollingInterval = null;

function updateAsyncProgressStep(stepId, status, message) {
    const step = document.getElementById(stepId);
    if (!step) return;
    
    step.classList.remove('active', 'completed', 'error');
    step.style.opacity = '1';
    
    if (status === 'active') {
        step.classList.add('active');
    } else if (status === 'completed') {
        step.classList.add('completed');
    } else if (status === 'error') {
        step.classList.add('error');
    }
    
    const statusDiv = step.querySelector('.step-status');
    if (statusDiv) {
        statusDiv.textContent = message || status;
    }
}

async function pollScanStatus() {
    const statusUrl = 'http://localhost:8002<?= htmlspecialchars($result['check_status_url']) ?>';
    try {
        const response = await fetch(statusUrl);
        const data = await response.json();
        
        const statusDiv = document.getElementById('async-status-message');
        statusDiv.textContent = `Status: ${data.status} (${data.progress_percent || 0}%) - ${data.phase || ''}`;
        
        // Update progress based on status
        if (data.status === 'in_progress') {
            const phase = data.phase || '';
            const percent = data.progress_percent || 0;
            
            if (phase === 'clone') {
                updateAsyncProgressStep('async-step-clone', 'active', `Klonowanie (${percent}%)`);
            } else if (phase === 'analyze') {
                updateAsyncProgressStep('async-step-clone', 'completed', 'Zakonczone');
                updateAsyncProgressStep('async-step-analyze', 'active', `Analiza (${percent}%)`);
            } else if (phase === 'complete') {
                updateAsyncProgressStep('async-step-clone', 'completed', 'Zakonczone');
                updateAsyncProgressStep('async-step-analyze', 'completed', 'Zakonczone');
                updateAsyncProgressStep('async-step-metrics', 'completed', 'Zakonczone');
                updateAsyncProgressStep('async-step-templates', 'active', `Generowanie (${percent}%)`);
            }
        } else if (data.status === 'completed') {
            updateAsyncProgressStep('async-step-templates', 'completed', 'Zakonczone');
            statusDiv.textContent = '✅ Skan zakonczony! Odswiez strone aby zobaczyc wyniki.';
            clearInterval(pollingInterval);
        } else if (data.status === 'failed') {
            updateAsyncProgressStep('async-step-clone', 'error', 'Blad: ' + (data.error?.message || 'Nieznany blad'));
            clearInterval(pollingInterval);
        }
    } catch (error) {
        console.error('Polling error:', error);
    }
}

// Start polling automatically
pollingInterval = setInterval(pollScanStatus, 2000);
pollScanStatus(); // Initial check
