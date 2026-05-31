// ===== PRELOADER =====
(function() {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        const hasSeen = localStorage.getItem('tb_seen_preloader');
        if (hasSeen) {
            preloader.style.display = 'none';
        } else {
            setTimeout(() => {
                preloader.classList.add('hidden');
                localStorage.setItem('tb_seen_preloader', '1');
            }, 2000);
        }
    }
})();

// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const y = window.scrollY;
    navbar.classList.toggle('scrolled', y > 50);
    lastScroll = y;
}, { passive: true });

// ===== MOBILE MENU =====
const mobileToggle = document.getElementById('mobileToggle');
const navLinks = document.getElementById('navLinks');
if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
        navLinks.classList.toggle('open');
        mobileToggle.classList.toggle('active');
    });
}

// ===== SMOOTH SCROLL FOR ANCHORS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        if (window.innerWidth <= 768 && navLinks) {
            navLinks.classList.remove('open');
            if (mobileToggle) mobileToggle.classList.remove('active');
        }
    });
});

// ===== COUNTER ANIMATION =====
function animateCounter(el, target, suffix, duration = 1500) {
    const start = performance.now();
    const isFloat = target % 1 !== 0;

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = eased * target;

        if (isFloat) {
            el.textContent = current.toFixed(1) + (suffix || '');
        } else {
            el.textContent = Math.floor(current) + (suffix || '');
        }
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    requestAnimationFrame(update);
}

// ===== TRUST BAR COUNTERS =====
const trustObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseFloat(el.dataset.target);
            const suffix = el.dataset.suffix || '';
            animateCounter(el, target, suffix);

            // Animate progress bar fill
            const fill = el.closest('.trust-item')?.querySelector('.trust-progress-mini-fill');
            if (fill) {
                fill.style.width = fill.dataset.width || '100%';
            }
            trustObserver.unobserve(el);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.trust-value[data-target]').forEach(el => {
    trustObserver.observe(el);
});

// ===== SCROLL REVEAL =====
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

document.querySelectorAll('.reveal').forEach(el => {
    revealObserver.observe(el);
});



// ===== PRICING TOGGLE =====
(function() {
    const toggle = document.querySelector('.pricing-toggle-switch');
    const labels = document.querySelectorAll('.pricing-toggle-label');
    const prices = document.querySelectorAll('.pricing-price');
    if (!toggle || !prices.length) return;

    const monthlyPrices = [];
    const yearlyPrices = [];

    prices.forEach(p => {
        const text = p.textContent.trim();
        monthlyPrices.push(text);
        // Simpler approach: store in data attrs
    });

    prices.forEach(p => {
        monthlyPrices.push(p.dataset.monthly || p.textContent.trim());
        yearlyPrices.push(p.dataset.yearly || p.textContent.trim());
    });

    toggle.addEventListener('click', () => {
        const isYearly = toggle.classList.toggle('active');
        labels.forEach(l => l.classList.toggle('active', l.dataset.period === (isYearly ? 'yearly' : 'monthly')));

        prices.forEach((p, i) => {
            p.style.opacity = '0';
            setTimeout(() => {
                p.innerHTML = isYearly ? yearlyPrices[i] : monthlyPrices[i];
                p.style.opacity = '1';
            }, 150);
        });
    });
})();

// ===== REVIEWS CAROUSEL =====
(function() {
    const track = document.querySelector('.reviews-track');
    const dots = document.querySelectorAll('.carousel-dot');
    const arrows = document.querySelectorAll('.carousel-arrow');
    if (!track) return;

    let current = 0;
    const total = track.children.length;

    function goTo(index) {
        if (index < 0) index = total - 1;
        if (index >= total) index = 0;
        current = index;
        track.style.transform = `translateX(-${current * 100}%)`;
        dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }

    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => goTo(i));
    });

    arrows.forEach(arrow => {
        arrow.addEventListener('click', () => {
            goTo(current + (arrow.dataset.dir === 'next' ? 1 : -1));
        });
    });

    // Auto-play
    let interval = setInterval(() => goTo(current + 1), 5000);

    track.addEventListener('mouseenter', () => clearInterval(interval));
    track.addEventListener('mouseleave', () => {
        clearInterval(interval);
        interval = setInterval(() => goTo(current + 1), 5000);
    });
})();

// ===== FAQ ACCORDION =====
function toggleFaq(btn) {
    const item = btn.closest('.faq-item');
    if (!item) return;

    // Close others
    document.querySelectorAll('.faq-item.active').forEach(el => {
        if (el !== item) el.classList.remove('active');
    });

    item.classList.toggle('active');
}

// ===== HERO STATS COUNTER =====
(function() {
    const heroStats = document.querySelectorAll('.hero-stat-value[data-target]');
    if (heroStats.length) {
        const heroObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    heroStats.forEach(el => {
                        const target = parseFloat(el.dataset.target);
                        const suffix = el.dataset.suffix || '';
                        animateCounter(el, target, suffix);
                    });
                    heroObserver.disconnect();
                }
            });
        }, { threshold: 0.3 });
        heroObserver.observe(heroStats[0].closest('.hero-stats') || heroStats[0]);
    }
})();

// ===== MAGNETIC BUTTONS =====
document.querySelectorAll('.btn-magnetic').forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.transform = '';
    });
});

// ===== ANALYTICS HELPERS =====
function trackCTA(action) {
    if (typeof ym !== 'undefined') {
        ym(109236208, 'reachGoal', action);
    }
    if (typeof gtag !== 'undefined') {
        gtag('event', 'click', { event_category: 'CTA', event_label: action });
    }
}

// Track CTA clicks
document.querySelectorAll('[data-track]').forEach(el => {
    el.addEventListener('click', () => trackCTA(el.dataset.track));
});

// ===== DASHBOARD CHART ANIMATION =====
(function() {
    const charts = document.querySelectorAll('.chart-bars');
    charts.forEach(chart => {
        const bars = chart.querySelectorAll('.chart-bar');
        bars.forEach(bar => {
            const h = bar.dataset.height || bar.style.height || '50%';
            bar.style.height = '0';
            setTimeout(() => {
                bar.style.height = h;
            }, 300);
        });
    });
})();

// ===== SKELETON TO REAL (Interface section) =====
(function() {
    const skeleton = document.querySelector('.dashboard-skeleton');
    if (skeleton) {
        const skeletonObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    skeleton.classList.add('skeleton-fade-in');
                    skeletonObserver.unobserve(skeleton);
                }
            });
        }, { threshold: 0.3 });
        skeletonObserver.observe(skeleton);
    }
})();

// ===== SERVICE WORKER REGISTRATION =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(reg => {
            console.log('SW registered:', reg.scope);
        }).catch(err => {
            console.warn('SW registration failed:', err);
        });
    });
}

// ===== AI SIMULATOR =====
(function() {
    var generateBtn = document.getElementById('simGenerateBtn');
    var resultContent = document.getElementById('simResultContent');
    var typingLine = document.getElementById('simTypingLine');
    var speedValue = document.getElementById('simSpeedValue');
    var styleBtns = document.querySelectorAll('.sim-style');
    var postText = document.getElementById('simPostText');
    var currentStyle = 'expert';

    styleBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            styleBtns.forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            currentStyle = btn.dataset.style;
        });
    });

    var comments = {
        expert: [
            'С точки зрения ончейн-аналитики, пробой $100k — это психологический уровень, а не технический. Коррекция на 15-20% после таких пробоев — стандарт. Входить лучше после ретеста зоны $85-90k. Если смотрите на долгосрок — DCA на каждом проседании.',
            'Институционалы фиксят прибыль на круглых цифрах. Смотрим на Open Interest и Funding Rate. Если OI падает — рынок перегрет. Мой прогноз: консолидация $90-105k в ближайшие 2 недели.',
            'Не торопитесь. $100k — это психологическая отметка, но фундаментально ничего не изменилось. Ждите подтверждения объёмами выше $105k, иначе сольётесь на коррекции.'
        ],
        toxic: [
            'Очередной нуб, который хочет купить на хае 🤡 Продавай свои альты, пока они не ушли в ноль. Зашёл бы ты в крипту в 2017 — был бы уже на Бали, а не спрашивал совета в телеге.',
            'Ты серьёзно? Когда биток бил ATH, ты сидел в стейблах? 😂 Твой поезд ушёл, чувак. Теперь только дождаться ликвидаций лонгистов и зайти на просадке. Без паники.',
            'Входить после х100? Гениально. С таким подходом ты будешь вечно покупать на хаях и сливать на лоях. Научись сначала читать график.'
        ],
        humor: [
            'Биток за $100k, а я всё ещё считаю, что 2 пиццы за 10k BTC — лучшая сделка в истории 🤝 Если серьёзно — иду в лонг, но стоп на 88к. Худшее, что может случиться — придётся майнить сатохи ногами 🏃‍♂️',
            'Памп уже случился, а моя бабушка только скачала Binance 👵📱 Заходить или нет? Если ты веришь в крипту — да. Если нет — ты всё ещё читаешь этот канал, так что веришь 😉',
            '$100k — это когда ты продал год назад на $30k и теперь смотришь на график как мем с собакой в горящей комнате 🔥 Входить можно, но только если готов к американским горкам. Пристегнитесь, дамы и господа 🎢'
        ]
    };

    generateBtn.addEventListener('click', function() {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
        resultContent.classList.remove('active');
        document.querySelector('.sim-result-empty').style.display = 'none';
        typingLine.textContent = '';
        resultContent.classList.add('active');

        var options = comments[currentStyle];
        var response = options[Math.floor(Math.random() * options.length)];
        var totalChars = response.length;
        var startTime = performance.now();
        var revealed = 0;

        // Simulate Cerebras-speed streaming (fast — ~200 tokens/s ≈ ~600+ chars/s)
        function typeNext() {
            if (revealed >= totalChars) {
                var elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
                var charsPerSec = Math.round(totalChars / parseFloat(elapsed));
                speedValue.textContent = charsPerSec;
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-bolt"></i> Сгенерировать ещё';
                return;
            }
            var chunkSize = Math.max(1, Math.floor(8 + Math.random() * 18));
            revealed = Math.min(revealed + chunkSize, totalChars);
            typingLine.textContent = response.substring(0, revealed);
            var charsPerSec = revealed / ((performance.now() - startTime) / 1000);
            speedValue.textContent = Math.round(charsPerSec);
            requestAnimationFrame(function() {
                setTimeout(typeNext, 8 + Math.random() * 12);
            });
        }
        typeNext();
    });
})();

// ===== LIVE ACTION COUNTER =====
(function() {
    var countEl = document.getElementById('liveActionCount');
    if (!countEl) return;
    var base = 142492;
    var shown = base;

    function updateCounter() {
        var increment = Math.floor(Math.random() * 7) + 1;
        shown += increment;
        countEl.textContent = shown.toLocaleString();
    }

    updateCounter();
    setInterval(updateCounter, 4000 + Math.random() * 3000);
})();

console.log('GRAMGPT — Landing initialized');
