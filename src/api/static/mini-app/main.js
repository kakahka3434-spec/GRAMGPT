const tg = window.Telegram.WebApp;

// Initialize app
tg.expand();
tg.ready();

// Apply theme colors
document.body.style.setProperty('--bg-color', tg.backgroundColor || '#f5f7fa');

// Simple Router Helper
function navigate(page) {
    window.location.href = page;
}

// Fetch analytics from our API
async function updateStats() {
    try {
        const response = await fetch('/api/v1/analytics/summary');
        const data = await response.json();
        if (document.getElementById('leads-count')) {
            document.getElementById('leads-count').innerText = data.leads_captured.toLocaleString();
        }
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }

    // Simulate crisis check
    setTimeout(() => {
        const alert = document.getElementById("crisis-alert");
        if(alert) alert.style.display = "block";
    }, 2000);
}

// On page load
window.addEventListener('DOMContentLoaded', () => {
    updateStats();
});
