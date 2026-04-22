// ============================================================
// Smart Kitchen Dashboard — WebSocket Client
// ============================================================

let ws = null;
let timerInterval = null;  // browser-side countdown
let timerSeconds = 0;

// ---------- CONNECTION ----------
function connect(host) {
    if (ws) {
        ws.onclose = null;
        ws.close();
    }
    ws = new WebSocket('ws://' + host + ':81');

    ws.onopen = function () {
        setConn(true);
        addAlert('info', 'Connected to ' + host);
    };

    ws.onmessage = function (e) {
        try { update(JSON.parse(e.data)); } catch (er) { console.error(er); }
    };

    ws.onclose = function () {
        setConn(false);
    };

    ws.onerror = function () { ws.close(); };
}

function startConnection() {
    var ip = document.getElementById('espIp').value.trim();
    if (!ip) {
        addAlert('warning', 'Please enter an IP Address');
        return;
    }
    addAlert('info', 'Connecting to ' + ip + '...');
    connect(ip);
}

function setConn(on) {
    var dot = document.querySelector('.status-dot');
    var txt = document.getElementById('connText');
    dot.className = 'status-dot ' + (on ? 'connected' : 'disconnected');
    txt.textContent = on ? 'Online' : 'Offline';
}

function toggleValveManually() {
    if (!ws || ws.readyState !== 1) {
        addAlert('warning', 'Connect to the system first!');
        return;
    }
    var el = document.getElementById('vlvState');
    if (el.textContent === 'OPEN') {
        ws.send('CLOSE_VALVE');
        addAlert('info', 'Sent manual command: CLOSE Valve');
    } else {
        ws.send('OPEN_VALVE');
        addAlert('info', 'Sent manual command: OPEN Valve');
    }
}

// ---------- UPDATE UI ----------
function update(d) {
    // Temperature
    var tv = document.getElementById('tempVal');
    var tc = document.getElementById('tempCard');
    var tb = document.getElementById('tempBar');
    tv.textContent = d.t.toFixed(1);
    tb.style.width = Math.min(d.t / 80 * 100, 100) + '%';
    tc.className = 'card' + (d.t > d.tt ? ' danger' : '');
    tb.style.background = d.t > d.tt ? 'var(--danger)' : 'var(--accent)';

    // Humidity
    var hv = document.getElementById('humVal');
    var hb = document.getElementById('humBar');
    if (d.h !== undefined && d.h !== null) {
        hv.textContent = String(Math.round(d.h));
        hb.style.width = Math.min(d.h, 100) + '%';
        hb.style.background = 'var(--accent)';
    }

    // Gas (PPM scale: 0-10000)
    var gv = document.getElementById('gasVal');
    var gc = document.getElementById('gasCard');
    var gb = document.getElementById('gasBar');
    gv.textContent = d.g;
    gb.style.width = Math.min(d.g / 10000 * 100, 100) + '%';
    gc.className = 'card' + (d.g > d.gt ? ' danger' : '');
    gb.style.background = d.g > d.gt ? 'var(--danger)' : 'var(--accent)';

    // Flame
    var fv = document.getElementById('flameVal');
    var fd = document.getElementById('flameDot');
    var fc = document.getElementById('flameCard');
    if (d.fl) {
        fv.textContent = 'FIRE!';
        fd.className = 'status-indicator danger';
        fc.className = 'card danger';
    } else {
        fv.textContent = 'Safe';
        fd.className = 'status-indicator safe';
        fc.className = 'card';
    }

    // Motion
    var mv = document.getElementById('motionVal');
    var md = document.getElementById('motionDot');
    if (d.m) {
        mv.textContent = 'Detected';
        md.className = 'status-indicator active';
    } else {
        mv.textContent = 'None';
        md.className = 'status-indicator';
    }

    // Actuators
    setState('fanState', d.fn, 'ON', 'OFF', false);
    setState('buzState', d.bz, 'ON', 'OFF', true);
    setState('vlvState', d.sv, 'OPEN', 'CLOSED', false);

    // Thresholds placeholders
    document.getElementById('gasThreshIn').placeholder = d.gt;
    document.getElementById('tempThreshIn').placeholder = d.tt;

    // Alert
    if (d.al) handleAlert(d.al);
}

function setState(id, on, onTxt, offTxt, isDanger) {
    var el = document.getElementById(id);
    el.textContent = on ? onTxt : offTxt;
    if (on) {
        el.className = 'act-state ' + (isDanger ? 'danger-on' : 'on');
    } else {
        el.className = 'act-state off';
    }
}

// ---------- TIMER (runs entirely in the browser) ----------
function updateTimerDisplay() {
    var el = document.getElementById('timerDisp');
    if (timerSeconds <= 0) {
        el.textContent = '00:00';
        el.style.color = 'var(--accent)';
        return;
    }
    var m = Math.floor(timerSeconds / 60);
    var s = timerSeconds % 60;
    el.textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');

    // Flash red when under 30 seconds
    if (timerSeconds <= 30) {
        el.style.color = 'var(--danger)';
    } else {
        el.style.color = 'var(--accent)';
    }
}

function startTimer() {
    var mins = parseInt(document.getElementById('timerIn').value);
    if (!mins || mins < 1) {
        addAlert('warning', 'Enter a valid number of minutes');
        return;
    }
    // Stop any existing timer
    if (timerInterval) clearInterval(timerInterval);

    timerSeconds = mins * 60;
    addAlert('info', 'Cooking timer started: ' + mins + ' min');
    updateTimerDisplay();

    timerInterval = setInterval(function () {
        timerSeconds--;
        updateTimerDisplay();

        if (timerSeconds <= 0) {
            clearInterval(timerInterval);
            timerInterval = null;
            timerSeconds = 0;
            updateTimerDisplay();

            // TIMER DONE — send CLOSE_VALVE command to Pico via ESP
            if (ws && ws.readyState === 1) {
                ws.send('CLOSE_VALVE');
            }
            addAlert('danger', 'Timer finished! Gas valve CLOSED.');
        }
    }, 1000);
}

function cancelTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    timerSeconds = 0;
    updateTimerDisplay();
    addAlert('info', 'Cooking timer cancelled');
}

// ---------- COMMANDS ----------
function sendCmd(cmd, val) {
    if (!val || !ws || ws.readyState !== 1) return;
    ws.send(cmd + ':' + val);
    addAlert('info', 'Sent ' + cmd + ' = ' + val);
}

// ---------- ALERTS ----------
function handleAlert(code) {
    var msgs = {
        'GAS_HIGH': '⚠️ Gas level exceeded threshold!',
        'FLAME': '🔥 Flame detected — valve closed!',
        'UNATTENDED': '🚨 Unattended stove — system shut down!'
    };
    addAlert('danger', msgs[code] || code);
}

function addAlert(type, msg) {
    var log = document.getElementById('alertLog');
    var now = new Date();
    var time = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
    var entry = document.createElement('div');
    entry.className = 'alert-entry ' + type;
    entry.innerHTML = '<span class="alert-time">' + time + '</span><span>' + msg + '</span>';
    log.insertBefore(entry, log.firstChild);
    while (log.children.length > 50) log.removeChild(log.lastChild);
}

// ---------- INIT ----------
// No auto-connect — user enters IP manually
