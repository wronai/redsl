function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
    });
    // Show selected
    document.getElementById(tabName).classList.remove('hidden');
    
    // Update tab styles
    document.querySelectorAll('.tab').forEach(el => {
        el.classList.remove('active');
    });
    event.target.classList.add('active');
}

function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.innerText;
        btn.innerText = 'OK Skopiowano!';
        btn.style.background = '#2196f3';
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.background = '#4caf50';
        }, 2000);
    });
}

function downloadMarkdown() {
    // Get current form data and add format=md parameter
    const form = document.querySelector('form');
    const formData = new FormData(form);
    formData.append('format', 'md');
    
    // Create form submission with format parameter
    const url = new URL(window.location.href);
    url.searchParams.set('format', 'md');
    
    // Submit form to get markdown
    fetch(url.toString(), {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = 'redsl_outreach_report.md';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    })
    .catch(error => console.error('Download error:', error));
}
