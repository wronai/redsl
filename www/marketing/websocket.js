const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = wsProtocol + '//localhost:8002/ws/cqrs/events';
let ws = null;
let wsConnected = false;

function updateProgressStep(stepId, status, message) {
    const step = document.getElementById(stepId);
    if (!step) {
        console.error('[Progress] Step element not found:', stepId);
        return;
    }
    
    console.log('[Progress] Updating step:', stepId, 'status:', status, 'message:', message);
    
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
    } else {
        console.error('[Progress] Status div not found for step:', stepId);
    }
}

let pollingInterval = null;

async function startPolling() {
    const repoUrl = '<?= htmlspecialchars($repoUrl) ?>';
    const statusUrl = `http://localhost:8002/cqrs/query/scan/status?repo_url=${encodeURIComponent(repoUrl)}`;
    
    console.log('[Polling] Starting polling for:', repoUrl);
    
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    pollingInterval = setInterval(async () => {
        try {
            console.log('[Polling] Checking status...');
            const response = await fetch(statusUrl);
            const data = await response.json();
            
            console.log('[Polling] Status data:', data);
            
            if (data.status === 'in_progress') {
                const phase = data.phase || '';
                const percent = data.progress_percent || 0;
                const message = data.message || '';
                
                console.log('[Polling] Phase:', phase, 'Percent:', percent);
                
                if (phase === 'clone') {
                    updateProgressStep('step-clone', 'active', message + ` (${percent}%)`);
                } else if (phase === 'analyze') {
                    updateProgressStep('step-clone', 'completed', 'Zakonczone');
                    updateProgressStep('step-analyze', 'active', message + ` (${percent}%)`);
                } else if (phase === 'complete') {
                    updateProgressStep('step-clone', 'completed', 'Zakonczone');
                    updateProgressStep('step-analyze', 'completed', 'Zakonczone');
                    updateProgressStep('step-metrics', 'completed', 'Zakonczone');
                    updateProgressStep('step-templates', 'active', message + ` (${percent}%)`);
                }
            } else if (data.status === 'completed') {
                console.log('[Polling] Scan completed');
                updateProgressStep('step-clone', 'completed', 'Zakonczone');
                updateProgressStep('step-analyze', 'completed', 'Zakonczone');
                updateProgressStep('step-metrics', 'completed', 'Zakonczone');
                updateProgressStep('step-templates', 'completed', 'Zakonczone');
                clearInterval(pollingInterval);
            } else if (data.status === 'failed') {
                console.error('[Polling] Scan failed:', data.error);
                updateProgressStep('step-clone', 'error', 'Blad: ' + (data.error?.message || 'Nieznany blad'));
                clearInterval(pollingInterval);
            }
        } catch (error) {
            console.error('[Polling] Error:', error);
        }
    }, 2000);
    
    // Initial check
    pollScanStatus();
}

async function pollScanStatus() {
    const repoUrl = '<?= htmlspecialchars($repoUrl) ?>';
    const statusUrl = `http://localhost:8002/cqrs/query/scan/status?repo_url=${encodeURIComponent(repoUrl)}`;
    
    try {
        console.log('[Polling] Initial status check');
        const response = await fetch(statusUrl);
        const data = await response.json();
        console.log('[Polling] Initial status:', data);
        
        if (data.status === 'in_progress') {
            const phase = data.phase || '';
            const percent = data.progress_percent || 0;
            const message = data.message || '';
            
            if (phase === 'clone') {
                updateProgressStep('step-clone', 'active', message + ` (${percent}%)`);
            } else if (phase === 'analyze') {
                updateProgressStep('step-clone', 'completed', 'Zakonczone');
                updateProgressStep('step-analyze', 'active', message + ` (${percent}%)`);
            } else if (phase === 'complete') {
                updateProgressStep('step-clone', 'completed', 'Zakonczone');
                updateProgressStep('step-analyze', 'completed', 'Zakonczone');
                updateProgressStep('step-metrics', 'completed', 'Zakonczone');
                updateProgressStep('step-templates', 'active', message + ` (${percent}%)`);
            }
        } else if (data.status === 'completed') {
            updateProgressStep('step-clone', 'completed', 'Zakonczone');
            updateProgressStep('step-analyze', 'completed', 'Zakonczone');
            updateProgressStep('step-metrics', 'completed', 'Zakonczone');
            updateProgressStep('step-templates', 'completed', 'Zakonczone');
        }
    } catch (error) {
        console.error('[Polling] Initial check error:', error);
    }
}

function connectWebSocket() {
    console.log('[WebSocket] Attempting to connect to:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('[WebSocket] Connection opened');
        wsConnected = true;
        
        const statusCard = document.getElementById('ws-status-card');
        const statusElement = document.getElementById('ws-status');
        
        if (statusCard) {
            statusCard.style.display = 'block';
            console.log('[WebSocket] Status card displayed');
        } else {
            console.error('[WebSocket] ws-status-card element not found');
        }
        
        if (statusElement) {
            statusElement.innerHTML = '<span style="color: green;">● Polaczono (CQRS Event Stream)</span>';
            console.log('[WebSocket] Status updated');
        } else {
            console.error('[WebSocket] ws-status element not found');
        }
        
        // Subscribe to scan aggregate
        const aggregateId = 'scan:<?= htmlspecialchars($repoUrl) ?>';
        console.log('[WebSocket] Subscribing to aggregate:', aggregateId);
        ws.send(JSON.stringify({type: 'subscribe', aggregate_id: aggregateId}));
        
        // Initialize progress
        updateProgressStep('step-clone', 'active', 'Rozpoczynanie...');
        
        // Start polling as fallback
        startPolling();
    };
    
    ws.onmessage = function(event) {
        console.log('[WebSocket] Message received, raw data:', event.data);
        const data = JSON.parse(event.data);
        const eventsDiv = document.getElementById('ws-events');
        
        console.log('[WebSocket] Parsed data type:', data.type);
        
        if (data.type === 'event') {
            const evt = data.data;
            const payload = evt.payload || {};
            console.log('[WebSocket] Event type:', evt.event_type);
            console.log('[WebSocket] Event payload:', payload);
            
            // Update progress based on event type
            if (evt.event_type === 'ScanStarted') {
                console.log('[WebSocket] ScanStarted event - updating clone step');
                updateProgressStep('step-clone', 'active', 'Klonowanie z ' + (payload.repo_url || 'repozytorium'));
            } else if (evt.event_type === 'ScanProgress') {
                const phase = payload.phase;
                const percent = payload.progress_percent || 0;
                const message = payload.message || '';
                console.log('[WebSocket] ScanProgress event - phase:', phase, 'percent:', percent, 'message:', message);
                
                if (phase === 'clone') {
                    updateProgressStep('step-clone', 'active', message + ` (${percent}%)`);
                } else if (phase === 'analyze') {
                    console.log('[WebSocket] Completing clone step, starting analyze');
                    updateProgressStep('step-clone', 'completed', 'Zakonczone');
                    updateProgressStep('step-analyze', 'active', message + ` (${percent}%)`);
                } else if (phase === 'complete') {
                    console.log('[WebSocket] Completing analyze and metrics, starting templates');
                    updateProgressStep('step-analyze', 'completed', 'Zakonczone');
                    updateProgressStep('step-metrics', 'completed', 'Zakonczone');
                    updateProgressStep('step-templates', 'active', message + ` (${percent}%)`);
                }
            } else if (evt.event_type === 'ScanCompleted') {
                console.log('[WebSocket] ScanCompleted event - all steps completed');
                updateProgressStep('step-templates', 'completed', 'Zakonczone');
            } else if (evt.event_type === 'ScanFailed') {
                console.error('[WebSocket] ScanFailed event:', payload.error_message);
                updateProgressStep('step-clone', 'error', 'Blad: ' + (payload.error_message || 'Nieznany blad'));
            }
            
            // Add to debug events
            if (eventsDiv) {
                const line = document.createElement('div');
                line.style.marginBottom = '4px';
                line.innerHTML = `<span style="color: #666;">${new Date().toLocaleTimeString()}</span> <strong>${evt.event_type}</strong>: ${JSON.stringify(payload).substring(0, 100)}`;
                eventsDiv.insertBefore(line, eventsDiv.firstChild);
            }
        } else if (data.type === 'connection.established') {
            console.log('[WebSocket] Connection established');
            const line = document.createElement('div');
            line.style.color = 'green';
            line.textContent = '>>> Polaczono z CQRS Event Store';
            if (eventsDiv) {
                eventsDiv.insertBefore(line, eventsDiv.firstChild);
            }
        } else {
            console.log('[WebSocket] Unknown message type:', data.type);
        }
    };
    
    ws.onerror = function(error) {
        console.error('[WebSocket] Error:', error);
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            statusElement.innerHTML = '<span style="color: red;">● Blad polaczenia WebSocket</span>';
        }
        updateProgressStep('step-clone', 'error', 'Blad polaczenia');
    };
    
    ws.onclose = function() {
        console.log('[WebSocket] Connection closed');
        wsConnected = false;
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            statusElement.innerHTML = '<span style="color: orange;">● Rozlaczono</span>';
        }
    };
}

// Auto-connect on page load
setTimeout(connectWebSocket, 500);
