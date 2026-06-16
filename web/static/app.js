/**
 * AI 桌宠 Agent — Web Dashboard JavaScript
 * Tab switching, Chart.js init, Toast system, interaction stubs
 */

// ═══════════════════════════════════════════════
// Tab Switching
// ═══════════════════════════════════════════════
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const panels  = document.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            // Update buttons
            tabBtns.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');

            // Update panels
            panels.forEach(p => p.classList.remove('active'));
            const panel = document.getElementById(`panel-${target}`);
            if (panel) {
                panel.classList.add('active');
                // Init charts on first visit
                if (target === 'sensors' && !window._chartsInit) {
                    initCharts();
                    window._chartsInit = true;
                }
            }
        });
    });
}

// ═══════════════════════════════════════════════
// Chat Interaction
// ═══════════════════════════════════════════════
function initChat() {
    const input = document.getElementById('chatInput');
    const btnSend = document.getElementById('btnSend');
    const messages = document.getElementById('chatMessages');

    function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // User message
        appendMessage('user', text);
        input.value = '';

        // Show typing indicator
        const typing = appendTypingIndicator();

        // Call real API
        fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text}),
        })
        .then(r => r.json())
        .then(data => {
            removeTypingIndicator(typing);
            if (data.success && data.data) {
                appendMessage('pet', data.data.reply || '嗯...');
            } else {
                appendMessage('pet', '抱歉，我暂时无法回复~');
            }
        })
        .catch(e => {
            removeTypingIndicator(typing);
            appendMessage('pet', '网络出错了，请稍后再试~');
            console.error('Chat error:', e);
        });
    }

    function appendMessage(role, text) {
        const now = new Date();
        const time = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;

        const msg = document.createElement('div');
        msg.className = `msg msg-${role}`;

        if (role === 'pet') {
            msg.innerHTML = `
                <div class="msg-avatar">🐾</div>
                <div class="msg-body">
                    <div class="msg-bubble">${escapeHtml(text)}</div>
                    <div class="msg-meta">${time}</div>
                </div>`;
        } else {
            msg.innerHTML = `
                <div class="msg-body">
                    <div class="msg-bubble">${escapeHtml(text)}</div>
                    <div class="msg-meta">${time}</div>
                </div>`;
        }

        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendTypingIndicator() {
        const msg = document.createElement('div');
        msg.className = 'msg msg-pet typing-msg';
        msg.innerHTML = `
            <div class="msg-avatar">🐾</div>
            <div class="msg-body">
                <div class="msg-bubble">
                    <span class="typing-dots"><span></span><span></span><span></span></span>
                </div>
            </div>`;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        return msg;
    }

    function removeTypingIndicator(el) {
        if (el && el.parentNode) el.remove();
    }

    btnSend.addEventListener('click', sendMessage);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ═══════════════════════════════════════════════
// Chart.js Initialization
// ═══════════════════════════════════════════════
function initCharts() {
    if (typeof Chart === 'undefined') return;

    const gridColor = 'rgba(60,50,40,0.06)';
    const chartFont = { family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" };

    // Generate mock data
    const now = new Date();
    const labels24h = [];
    const tempData = [];
    const humiData = [];
    for (let i = 24; i >= 0; i--) {
        const t = new Date(now.getTime() - i * 3600000);
        labels24h.push(t);
        tempData.push(22 + Math.sin(i / 4) * 3 + Math.random() * 0.5);
        humiData.push(55 + Math.cos(i / 3) * 10 + Math.random() * 2);
    }

    // Temperature chart
    new Chart(document.getElementById('tempChart'), {
        type: 'line',
        data: {
            labels: labels24h,
            datasets: [{
                label: '温度 (°C)',
                data: tempData,
                borderColor: '#c8883a',
                backgroundColor: 'rgba(200,136,58,0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'hour', displayFormats: { hour: 'HH:mm' } },
                    grid: { color: gridColor },
                    ticks: { color: '#a89e95', font: { ...chartFont, size: 11 } },
                },
                y: {
                    suggestedMin: 15, suggestedMax: 35,
                    grid: { color: gridColor },
                    ticks: { color: '#a89e95', font: { ...chartFont, size: 11 } },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index', intersect: false },
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
        }
    });

    // Humidity chart
    new Chart(document.getElementById('humiChart'), {
        type: 'line',
        data: {
            labels: labels24h,
            datasets: [{
                label: '湿度 (%RH)',
                data: humiData,
                borderColor: '#4a9aab',
                backgroundColor: 'rgba(74,154,171,0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'hour', displayFormats: { hour: 'HH:mm' } },
                    grid: { color: gridColor },
                    ticks: { color: '#a89e95', font: { ...chartFont, size: 11 } },
                },
                y: {
                    suggestedMin: 30, suggestedMax: 90,
                    grid: { color: gridColor },
                    ticks: { color: '#a89e95', font: { ...chartFont, size: 11 } },
                }
            },
            plugins: { legend: { display: false } },
        }
    });

    // Mood timeline (custom canvas)
    initMoodTimeline();
}

function initMoodTimeline() {
    const canvas = document.getElementById('moodChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(dpr, dpr);

    const moodColors = {
        happy:   '#c49a2a',
        curious: '#4a9aab',
        sleepy:  '#8b72b8',
        alert:   '#c06058',
        chatty:  '#5a9e6f',
        calm:    '#5b8a9a',
        lonely:  '#7b6fb0',
    };

    // Mock mood data for last 24h
    const moods = ['sleepy','sleepy','sleepy','calm','calm','happy','happy','chatty',
                   'chatty','happy','curious','happy','calm','chatty','happy','alert',
                   'happy','calm','calm','sleepy','sleepy','lonely','lonely','calm'];

    const w = rect.width;
    const h = rect.height;
    const barH = 32;
    const y0 = (h - barH) / 2;
    const segW = w / moods.length;

    // Draw mood segments
    moods.forEach((mood, i) => {
        ctx.fillStyle = moodColors[mood] || '#333';
        ctx.globalAlpha = 0.7;
        ctx.fillRect(i * segW, y0, segW - 1, barH);
    });
    ctx.globalAlpha = 1;

    // Time labels
    ctx.fillStyle = '#a89e95';
    ctx.font = '11px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    [0, 6, 12, 18, 23].forEach(h => {
        ctx.fillText(`${String(h).padStart(2,'0')}:00`, h * segW + segW / 2, y0 + barH + 16);
    });

    // Mood legend
    ctx.textAlign = 'left';
    const legendY = y0 - 10;
    let lx = 0;
    Object.entries(moodColors).forEach(([name, color]) => {
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.7;
        ctx.fillRect(lx, legendY - 4, 10, 10);
        ctx.globalAlpha = 1;
        ctx.fillStyle = '#7a716a';
        const labels = {happy:'开心',curious:'好奇',sleepy:'困倦',alert:'警觉',chatty:'健谈',calm:'平静',lonely:'孤独'};
        ctx.fillText(labels[name] || name, lx + 14, legendY + 5);
        lx += ctx.measureText(labels[name] || name).width + 28;
    });
}

// ═══════════════════════════════════════════════
// Toast Notification System
// ═══════════════════════════════════════════════
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    const icons = {
        success: '✅',
        info:    '🔔',
        warning: '⚠️',
        error:   '❌',
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || '🔔'}</span>
        <span class="toast-msg">${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="关闭">×</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => removeToast(toast));
    container.appendChild(toast);

    setTimeout(() => removeToast(toast), duration);
}

function removeToast(toast) {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 200);
}

// ═══════════════════════════════════════════════
// Reminder Form Toggle
// ═══════════════════════════════════════════════
function initReminders() {
    const btnAdd = document.getElementById('btnAddReminder');
    const btnCancel = document.getElementById('btnCancelReminder');
    const form = document.getElementById('reminderForm');

    if (!btnAdd || !form) return;

    btnAdd.addEventListener('click', () => {
        form.style.display = form.style.display === 'none' ? 'flex' : 'none';
    });
    btnCancel.addEventListener('click', () => {
        form.style.display = 'none';
    });
}

// ═══════════════════════════════════════════════
// Range Button Group
// ═══════════════════════════════════════════════
function initRangeButtons() {
    document.querySelectorAll('.range-btn-group').forEach(group => {
        group.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                group.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // TODO: fetch new data from API
                showToast(`切换到 ${btn.textContent} 视图`, 'info', 1500);
            });
        });
    });
}

// ═══════════════════════════════════════════════
// WebSocket Placeholder
// ═══════════════════════════════════════════════
function initWebSocket() {
    // TODO: Connect to ws://pi-ip:8000/ws
    // On message: update sensor values, chat messages, mood state
    console.log('[WS] WebSocket placeholder — will connect to /ws on Raspberry Pi');
}

// ═══════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initChat();
    initReminders();
    initRangeButtons();
    initWebSocket();
    initSettings();
    initVoiceInput();
    console.log('[智居物语] Dashboard ready');
});

// ═══════════════════════════════════════════════
// Greeting Rotation + Live Clock
// ═══════════════════════════════════════════════
const greetings = [
    '愿你今天被温柔以待',
    '今天也要元气满满哦',
    '记得喝杯热水',
    '你笑起来真好看',
    '一切都会顺利的',
    '今天也要好好吃饭',
    '你是最棒的',
    '累了就休息一下吧',
    '保持好心情很重要',
    '今天的你也很努力呢',
];

function updateClock() {
    const el = document.getElementById('headerTimeText');
    if (!el) return;
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    el.textContent = `${h}:${m}`;
}

function rotateGreeting() {
    const el = document.getElementById('headerGreeting');
    if (!el) return;
    const idx = Math.floor(Math.random() * greetings.length);
    el.textContent = greetings[idx];
}

// Init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 10000);
    setInterval(rotateGreeting, 30000);
});

// ═══════════════════════════════════════════════
// Settings Modal — LLM Configuration
// ═══════════════════════════════════════════════
function initSettings() {
    const modal = document.getElementById('settingsModal');
    const btnOpen = document.getElementById('btnSettings');
    const btnClose = document.getElementById('btnCloseSettings');
    const btnCancel = document.getElementById('btnCancelSettings');
    const btnSave = document.getElementById('btnSaveSettings');
    const btnTest = document.getElementById('btnTestConnection');
    const btnFetch = document.getElementById('btnFetchModels');
    const btnToggleKey = document.getElementById('btnToggleKey');
    const slider = document.getElementById('llmTemperature');
    const tempVal = document.getElementById('tempValue');

    if (!modal) return;

    // Open/close
    btnOpen?.addEventListener('click', () => {
        modal.style.display = 'flex';
        loadLLMSettings();
    });
    const closeModal = () => { modal.style.display = 'none'; };
    btnClose?.addEventListener('click', closeModal);
    btnCancel?.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // Temperature slider
    slider?.addEventListener('input', () => {
        if (tempVal) tempVal.textContent = slider.value;
    });

    // Toggle API key visibility
    btnToggleKey?.addEventListener('click', () => {
        const inp = document.getElementById('llmApiKey');
        if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
    });

    // Provider preset change
    document.getElementById('llmProvider')?.addEventListener('change', function() {
        const presets = window._llmPresets || {};
        const p = presets[this.value];
        if (p) {
            const url = document.getElementById('llmBaseUrl');
            const model = document.getElementById('llmModel');
            if (url && p.base_url) url.value = p.base_url;
            if (model && p.default_model) {
                model.innerHTML = `<option value="${p.default_model}">${p.default_model}</option>`;
            }
        }
    });

    // Fetch models
    btnFetch?.addEventListener('click', fetchModels);

    // Test connection
    btnTest?.addEventListener('click', testConnection);

    // STT
    document.getElementById('btnTestStt')?.addEventListener('click', testSttConnection);
    document.getElementById('btnToggleSttKey')?.addEventListener('click', () => {
        const inp = document.getElementById('sttApiKey');
        if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
    });

    // Save
    btnSave?.addEventListener('click', saveLLMSettings);
}

async function loadLLMSettings() {
    try {
        const resp = await fetch('/api/settings/llm');
        const data = await resp.json();
        if (!data.success) return;

        const cfg = data.data;
        window._llmPresets = data.presets || {};

        const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
        setVal('llmProvider', cfg.provider || 'deepseek');
        setVal('llmBaseUrl', cfg.base_url);
        setVal('llmApiKey', cfg.api_key === '****' ? '' : cfg.api_key);
        setVal('llmTemperature', cfg.temperature || 0.7);
        setVal('llmMaxTokens', cfg.max_tokens || 512);

        const tempVal = document.getElementById('tempValue');
        if (tempVal) tempVal.textContent = cfg.temperature || 0.7;

        // If model is set, show it
        const modelSel = document.getElementById('llmModel');
        if (modelSel && cfg.model) {
            modelSel.innerHTML = `<option value="${escapeHtml(cfg.model)}">${escapeHtml(cfg.model)}</option>`;
        }

        showToast('配置已加载', 'info', 1500);
        loadSTTSettings();  // 同时加载 STT 配置
    } catch (e) {
        console.error('Load settings error:', e);
    }
}

async function saveLLMSettings() {
    const getVal = id => { const el = document.getElementById(id); return el ? el.value : ''; };

    const cfg = {
        provider: getVal('llmProvider'),
        base_url: getVal('llmBaseUrl'),
        api_key: getVal('llmApiKey'),
        model: getVal('llmModel'),
        temperature: parseFloat(getVal('llmTemperature')) || 0.7,
        max_tokens: parseInt(getVal('llmMaxTokens')) || 512,
    };

    // Don't save empty key (preserve existing)
    if (!cfg.api_key || cfg.api_key.includes('****')) {
        delete cfg.api_key;
    }

    try {
        const resp = await fetch('/api/settings/llm', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(cfg),
        });
        const data = await resp.json();
        if (data.success) {
            await saveSTTSettings();  // 同时保存 STT 配置
            showToast('配置已保存 ✓', 'success');
            document.getElementById('settingsModal').style.display = 'none';
        } else {
            showToast('保存失败: ' + (data.error || ''), 'error');
        }
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function fetchModels() {
    const btn = document.getElementById('btnFetchModels');
    const sel = document.getElementById('llmModel');
    if (!btn || !sel) return;

    // 先保存当前配置，确保 API Key 生效
    const getVal = id => { const el = document.getElementById(id); return el ? el.value : ''; };
    const apiKey = getVal('llmApiKey');
    if (!apiKey || apiKey.includes('****')) {
        showToast('请先输入 API Key', 'warning');
        return;
    }

    btn.disabled = true;
    btn.textContent = '加载中...';
    sel.innerHTML = '<option>正在获取...</option>';

    // 先保存配置
    try {
        await fetch('/api/settings/llm', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                provider: getVal('llmProvider'),
                base_url: getVal('llmBaseUrl'),
                api_key: apiKey,
                model: getVal('llmModel'),
                temperature: parseFloat(getVal('llmTemperature')) || 0.7,
                max_tokens: parseInt(getVal('llmMaxTokens')) || 512,
            }),
        });
    } catch (_) {}

    // 再获取模型
    try {
        const resp = await fetch('/api/settings/llm/models');
        const data = await resp.json();
        if (data.success && data.data.length > 0) {
            sel.innerHTML = '';
            data.data.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.id;
                sel.appendChild(opt);
            });
            showToast(`已加载 ${data.data.length} 个模型`, 'success');
        } else {
            sel.innerHTML = '<option value="">无可用模型</option>';
            showToast('未获取到模型: ' + (data.error || '请检查 API Key'), 'warning');
        }
    } catch (e) {
        sel.innerHTML = '<option value="">获取失败</option>';
        showToast('获取模型失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '获取模型';
    }
}

async function testConnection() {
    const btn = document.getElementById('btnTestConnection');
    const statusEl = document.getElementById('connectionStatus');
    if (!btn || !statusEl) return;

    // Save first so test uses current values
    const getVal = id => { const el = document.getElementById(id); return el ? el.value : ''; };
    const cfg = {
        provider: getVal('llmProvider'),
        base_url: getVal('llmBaseUrl'),
        api_key: getVal('llmApiKey'),
        model: getVal('llmModel'),
        temperature: parseFloat(getVal('llmTemperature')) || 0.7,
        max_tokens: parseInt(getVal('llmMaxTokens')) || 512,
    };
    if (!cfg.api_key || cfg.api_key.includes('****')) delete cfg.api_key;

    // Save config before testing
    try {
        await fetch('/api/settings/llm', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(cfg),
        });
    } catch (_) {}

    btn.disabled = true;
    btn.textContent = '⏳ 测试中...';
    statusEl.innerHTML = '<span class="status-dot status-loading"></span><span class="status-text">连接中...</span>';

    try {
        const resp = await fetch('/api/settings/llm/test', { method: 'POST' });
        const data = await resp.json();
        const d = data.data || {};

        if (d.success) {
            statusEl.innerHTML = `<span class="status-dot status-ok"></span><span class="status-text">✓ ${d.message} · ${d.latency_ms}ms · ${d.model}</span>`;
            showToast('连接成功 ✓', 'success');
        } else {
            statusEl.innerHTML = `<span class="status-dot status-error"></span><span class="status-text">✗ ${d.message}</span>`;
            showToast('连接失败', 'error');
        }
    } catch (e) {
        statusEl.innerHTML = `<span class="status-dot status-error"></span><span class="status-text">✗ ${e.message}</span>`;
        showToast('测试失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔗 测试连接';
    }
}

// ═══════════════════════════════════════════════
// STT 语音识别配置 + 麦克风录音
// ═══════════════════════════════════════════════

// 加载 STT 配置（在 loadLLMSettings 中调用）
async function loadSTTSettings() {
    try {
        const resp = await fetch('/api/settings/stt');
        const data = await resp.json();
        if (!data.success) return;
        const cfg = data.data;
        const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
        setVal('sttProvider', cfg.provider || 'openai');
        setVal('sttBaseUrl', cfg.base_url);
        setVal('sttApiKey', cfg.api_key === '****' ? '' : cfg.api_key);
        setVal('sttModel', cfg.model || 'whisper-1');
        setVal('sttLanguage', cfg.language || 'zh');
    } catch (e) { console.error('Load STT settings error:', e); }
}

async function saveSTTSettings() {
    const getVal = id => { const el = document.getElementById(id); return el ? el.value : ''; };
    const cfg = {
        provider: getVal('sttProvider'),
        base_url: getVal('sttBaseUrl'),
        api_key: getVal('sttApiKey'),
        model: getVal('sttModel'),
        language: getVal('sttLanguage'),
    };
    if (!cfg.api_key || cfg.api_key.includes('****')) delete cfg.api_key;
    try {
        await fetch('/api/settings/stt', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(cfg),
        });
    } catch (e) { console.error('Save STT error:', e); }
}

// 测试 STT 连接
async function testSttConnection() {
    const btn = document.getElementById('btnTestStt');
    const statusEl = document.getElementById('sttStatus');
    if (!btn || !statusEl) return;

    await saveSTTSettings();
    btn.disabled = true;
    btn.textContent = '⏳ 测试中...';
    statusEl.innerHTML = '<span class="status-dot status-loading"></span><span class="status-text">连接中...</span>';

    try {
        const resp = await fetch('/api/settings/stt/test', { method: 'POST' });
        const data = await resp.json();
        const d = data.data || {};
        if (d.success) {
            statusEl.innerHTML = `<span class="status-dot status-ok"></span><span class="status-text">✓ ${d.message} · ${d.latency_ms}ms</span>`;
        } else {
            statusEl.innerHTML = `<span class="status-dot status-error"></span><span class="status-text">✗ ${d.message}</span>`;
        }
    } catch (e) {
        statusEl.innerHTML = `<span class="status-dot status-error"></span><span class="status-text">✗ ${e.message}</span>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🔗 测试 STT';
    }
}

// ─── 麦克风录音 → STT 识别 ───────────────────
let _mediaRecorder = null;
let _audioChunks = [];
let _isRecording = false;

function initVoiceInput() {
    const btnVoice = document.getElementById('btnVoice');
    if (!btnVoice) return;

    btnVoice.addEventListener('click', async () => {
        if (_isRecording) {
            stopRecording();
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            _mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
            _audioChunks = [];

            _mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) _audioChunks.push(e.data);
            };

            _mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blob = new Blob(_audioChunks, { type: 'audio/webm' });
                await uploadAudioForSTT(blob);
            };

            _mediaRecorder.start();
            _isRecording = true;
            btnVoice.classList.add('recording');
            btnVoice.textContent = '⏹️';
            showToast('🎤 正在录音...', 'info', 99999);
        } catch (e) {
            showToast('麦克风权限被拒绝', 'error');
        }
    });
}

function stopRecording() {
    if (_mediaRecorder && _isRecording) {
        _mediaRecorder.stop();
        _isRecording = false;
        const btnVoice = document.getElementById('btnVoice');
        if (btnVoice) {
            btnVoice.classList.remove('recording');
            btnVoice.textContent = '🎤';
        }
        // 移除录音 toast
        document.querySelectorAll('.toast').forEach(t => {
            if (t.textContent.includes('正在录音')) t.remove();
        });
    }
}

async function uploadAudioForSTT(blob) {
    showToast('正在识别语音...', 'info', 5000);
    const input = document.getElementById('chatInput');

    try {
        const formData = new FormData();
        formData.append('audio', blob, 'voice.webm');

        const resp = await fetch('/api/stt/recognize', { method: 'POST', body: formData });
        const data = await resp.json();

        if (data.success && data.data?.text) {
            const text = data.data.text;
            if (input) input.value = text;
            showToast('语音识别完成', 'success', 2000);
        } else {
            showToast('语音识别失败: ' + (data.error || '未知错误'), 'error');
        }
    } catch (e) {
        showToast('语音识别出错: ' + e.message, 'error');
    }
}
