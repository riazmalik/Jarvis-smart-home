// ===== State =====
let bulbStates = [false, false, false, false];
const ESP32_IP = "YOUR_ESP32_IP"; // Change this!

// ===== Update UI =====
function updateUI() {
    const onCount = bulbStates.filter(v => v).length;
    document.getElementById('bulbCount').textContent = onCount + '/4';
    
    ['living', 'bedroom', 'kitchen', 'study'].forEach((name, i) => {
        const btn = document.getElementById('btn-' + name);
        const status = document.getElementById('status-' + name);
        
        if (bulbStates[i]) {
            btn.className = 'btn on';
            status.textContent = 'آن';
        } else {
            btn.className = 'btn off';
            status.textContent = 'بند';
        }
    });
}

// ===== Toggle Bulb =====
function toggleBulb(index) {
    bulbStates[index] = !bulbStates[index];
    updateUI();
    
    const state = bulbStates[index] ? 'on' : 'off';
    fetch(`/api/bulb?index=${index}&state=${state}`)
        .then(() => addLog('لائٹ ' + (bulbStates[index] ? 'آن' : 'بند'), 'urdu'))
        .catch(err => console.log('ESP32 error'));
}

// ===== All On/Off =====
function allOn() {
    bulbStates = [true, true, true, true];
    updateUI();
    fetch('/api/bulb?all=on')
        .then(() => addLog('سب لائٹس آن', 'urdu'));
}

function allOff() {
    bulbStates = [false, false, false, false];
    updateUI();
    fetch('/api/bulb?all=off')
        .then(() => addLog('سب لائٹس بند', 'urdu'));
}

// ===== Voice Command =====
function sendVoice(command) {
    fetch('/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: command })
    })
    .then(response => response.json())
    .then(data => {
        addLog('🎤 ' + command, 'urdu');
        if (data.success) {
            if (command.includes('آن')) {
                bulbStates = [true, true, true, true];
            } else if (command.includes('بند')) {
                bulbStates = [false, false, false, false];
            }
            updateUI();
        }
    })
    .catch(err => console.log('Error:', err));
}

// ===== Add Log =====
function addLog(msg, type = '') {
    const container = document.getElementById('logContainer');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    const time = new Date().toLocaleTimeString('ur-PK');
    entry.innerHTML = `<span class="time">[${time}]</span> <span class="${type}">${msg}</span>`;
    container.appendChild(entry);
    if (container.children.length > 20) container.removeChild(container.firstChild);
    container.scrollTop = container.scrollHeight;
}

// ===== Fetch Status =====
function fetchStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.bulbs) {
                bulbStates = data.bulbs;
                updateUI();
            }
        })
        .catch(err => console.log('Error fetching status'));
}

// ===== Initial Load =====
fetchStatus();
addLog('🕌 جاروس ویب انٹرفیس لوڈ ہو گیا', 'urdu');

// Auto-refresh status every 5 seconds
setInterval(fetchStatus, 5000);