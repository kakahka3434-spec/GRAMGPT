// ============================================================
// GRAMGPT Mini App Framework
// ============================================================
;(function() {
    'use strict';

    // ===== Telegram WebApp Init =====
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    // Adapt to Telegram theme
    const theme = tg.colorScheme || 'dark';
    document.documentElement.setAttribute('data-theme', theme);

    const user = tg.initDataUnsafe?.user;
    if (user) {
        const el = document.getElementById('user-name');
        if (el) el.innerText = user.first_name;
    }

    // ===== Haptic feedback helper =====
    function haptic(type) {
        try { tg.HapticFeedback.impactOccurred(type || 'medium'); } catch(e) {}
    }

    // ============================================================
    // API Client
    // ============================================================
    const api = {
        baseURL: '/api/v1',

        async request(method, path, body) {
            const opts = {
                method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) opts.body = JSON.stringify(body);
            try {
                const res = await fetch(`${this.baseURL}${path}`, opts);
                if (!res.ok) {
                    const err = await res.json().catch(() => ({ detail: res.statusText }));
                    throw new Error(err.detail || `HTTP ${res.status}`);
                }
                return await res.json();
            } catch (err) {
                throw err;
            }
        },

        get(path) { return this.request('GET', path); },
        post(path, body) { return this.request('POST', path, body); },
        patch(path, body) { return this.request('PATCH', path, body); },
        del(path) { return this.request('DELETE', path); },

        async fetchWithLoading(path, targetEl, renderFn) {
            const el = typeof targetEl === 'string' ? document.getElementById(targetEl) : targetEl;
            if (!el) return;
            // Show skeleton
            el.innerHTML = '<div class="skeleton-card"><div class="skeleton-title"></div><div class="skeleton-text"></div><div class="skeleton-text-sm"></div></div>';
            try {
                const data = await this.get(path);
                el.innerHTML = '';
                renderFn(el, data);
            } catch (err) {
                el.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h4>Ошибка загрузки</h4><p>${err.message}</p></div>`;
            }
        }
    };

    // ============================================================
    // Toast Notification System
    // ============================================================
    function createToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    function toast(type, title, message, duration) {
        haptic('medium');
        const container = createToastContainer();
        duration = duration || 4000;

        const el = document.createElement('div');
        el.className = `toast toast-${type}`;

        const icons = { success: 'check-circle', error: 'times-circle', warning: 'exclamation-triangle', info: 'info-circle' };
        el.innerHTML = `
            <div class="toast-icon"><i class="fas fa-${icons[type] || 'info-circle'}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
            <button class="toast-close" onclick="this.parentElement.classList.add('toast-exit');setTimeout(()=>this.parentElement.remove(),300)"><i class="fas fa-times"></i></button>
        `;
        container.appendChild(el);

        setTimeout(() => {
            el.classList.add('toast-exit');
            setTimeout(() => el.remove(), 300);
        }, duration);
    }

    // ============================================================
    // Modal Dialog System
    // ============================================================
    function showModal(title, text, confirmText, cancelText, onConfirm) {
        haptic('medium');
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">${title}</div>
                <div class="modal-text">${text}</div>
                <div class="modal-actions">
                    <button class="btn btn-secondary btn-sm modal-cancel">${cancelText || 'Отмена'}</button>
                    <button class="btn btn-sm modal-confirm">${confirmText || 'Подтвердить'}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector('.modal-cancel').addEventListener('click', () => overlay.remove());
        overlay.querySelector('.modal-close')?.addEventListener('click', () => overlay.remove());
        overlay.querySelector('.modal-confirm').addEventListener('click', () => {
            overlay.remove();
            if (onConfirm) onConfirm();
        });
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    }

    // ============================================================
    // Connection Monitor
    // ============================================================
    function initConnectionMonitor() {
        let bar = document.querySelector('.connection-bar');
        if (!bar) {
            bar = document.createElement('div');
            bar.className = 'connection-bar';
            document.body.prepend(bar);
        }

        window.addEventListener('online', () => {
            bar.className = 'connection-bar online';
            bar.textContent = '✅ Соединение восстановлено';
            setTimeout(() => { bar.textContent = ''; bar.className = 'connection-bar'; }, 2500);
        });
        window.addEventListener('offline', () => {
            bar.className = 'connection-bar offline';
            bar.textContent = '⚠️ Нет соединения с интернетом';
        });
    }

    // ============================================================
    // Navigation — set active nav item
    // ============================================================
    function setActiveNav(page) {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.toggle('active', el.getAttribute('href')?.includes(page));
        });
    }

    // ============================================================
    // Expose to window
    // ============================================================
    window.api = api;
    window.toast = toast;
    window.showModal = showModal;
    window.haptic = haptic;
    window.tg = tg;
    window.setActiveNav = setActiveNav;

    // ============================================================
    // Auto-init
    // ============================================================
    document.addEventListener('DOMContentLoaded', () => {
        initConnectionMonitor();
        // Auto-update stats on dashboard/home pages
        if (document.getElementById('leads-count')) {
            updateStats();
        }
        setTimeout(() => checkCrisisAlert(), 1500);
    });

    // ===== Legacy functions (preserved for backward compat) =====
    async function updateStats() {
        try {
            const data = await api.get('/analytics/summary');
            const leadsEl = document.getElementById('leads-count');
            if (leadsEl) leadsEl.innerText = Number(data.leads_captured || data.total_accounts).toLocaleString();
            const accountsEl = document.getElementById('accounts-count');
            if (accountsEl) accountsEl.innerText = data.active_accounts || data.total_accounts;
            const roiEl = document.getElementById('roi-value');
            if (roiEl) roiEl.innerText = data.roi_average || 'N/A';
        } catch (e) {
            console.error('Stats fetch error:', e);
        }
    }

    function checkCrisisAlert() {
        const riskStatus = 'safe';
        if (riskStatus !== 'safe') {
            const alert = document.getElementById('crisis-alert');
            if (alert) alert.style.display = 'block';
        }
    }
})();
