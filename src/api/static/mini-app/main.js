const tg = window.Telegram.WebApp;

tg.expand();
tg.ready();

const user = tg.initDataUnsafe?.user;
if (user) {
    const el = document.getElementById('user-name');
    if (el) el.innerText = user.first_name;
}

async function updateStats() {
    try {
        const response = await fetch('/api/v1/analytics/summary');
        if (!response.ok) return;
        const data = await response.json();

        const leadsEl = document.getElementById('leads-count');
        if (leadsEl) leadsEl.innerText = Number(data.leads_captured).toLocaleString();

        const accountsEl = document.getElementById('accounts-count');
        if (accountsEl) accountsEl.innerText = data.active_accounts;

        const roiEl = document.getElementById('roi-value');
        if (roiEl) roiEl.innerText = data.roi_average;
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
}

function checkCrisisAlert() {
    const riskStatus = 'safe';
    if (riskStatus !== 'safe') {
        const alert = document.getElementById("crisis-alert");
        if (alert) alert.style.display = "block";
    }
}

window.addEventListener('DOMContentLoaded', () => {
    updateStats();
    setTimeout(checkCrisisAlert, 1500);
});
