// app.js — Empathy Engine Frontend Logic

const EMOTION_EMOJIS = {
  joy: '😊', sadness: '😢', anger: '😠',
  fear: '😨', disgust: '🤢', surprise: '😲', neutral: '😐'
};

let currentAudioUrl = null;

// ── Character counter ──
const inputText = document.getElementById('inputText');
inputText.addEventListener('input', () => {
  document.getElementById('charCount').textContent = inputText.value.length;
});

// ── Example chips ──
function fillExample(btn) {
  inputText.value = btn.textContent;
  document.getElementById('charCount').textContent = btn.textContent.length;
}

// ── Loading state ──
function setLoading(msg) {
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('loadingText').textContent = msg;
}
function clearLoading() {
  document.getElementById('loadingOverlay').style.display = 'none';
}

// ── Analyze only ──
async function analyzeOnly() {
  const text = inputText.value.trim();
  if (!text) { alert('Please enter some text first.'); return; }

  setLoading('Detecting emotion…');
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('synthesizeBtn').disabled = true;

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis failed.');
    showEmotionResults(data, false);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    clearLoading();
    document.getElementById('analyzeBtn').disabled = false;
    document.getElementById('synthesizeBtn').disabled = false;
  }
}

// ── Full synthesize ──
async function synthesize() {
  const text = inputText.value.trim();
  if (!text) { alert('Please enter some text first.'); return; }

  setLoading('Synthesizing voice…');
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('synthesizeBtn').disabled = true;

  try {
    const res = await fetch('/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Synthesis failed.');

    // Build analysis-like object for display
    const display = {
      emotion: data.emotion,
      intensity: data.intensity,
      confidence: data.analysis.confidence,
      all_scores: data.analysis.all_scores,
      polarity: data.analysis.polarity,
      subjectivity: data.analysis.subjectivity,
      voice_config: data.voice_config
    };
    showEmotionResults(display, true);
    showAudio(data.audio_url);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    clearLoading();
    document.getElementById('analyzeBtn').disabled = false;
    document.getElementById('synthesizeBtn').disabled = false;
  }
}

// ── Render emotion results ──
function showEmotionResults(data, showVoice) {
  const card = document.getElementById('emotionCard');
  card.style.display = 'block';

  const emoji = EMOTION_EMOJIS[data.emotion] || '🤖';
  const color = data.voice_config?.color || '#9B9B9B';

  document.getElementById('emotionEmoji').textContent = emoji;
  document.getElementById('emotionLabel').textContent = data.voice_config?.description || data.emotion;
  const badge = document.getElementById('emotionBadge');
  badge.style.borderColor = color;
  badge.style.background = hexToRgba(color, 0.15);
  badge.style.color = color;

  animateBar('confidenceBar', data.confidence * 100);
  document.getElementById('confidenceVal').textContent = Math.round(data.confidence * 100) + '%';

  animateBar('intensityBar', data.intensity * 100);
  document.getElementById('intensityVal').textContent = Math.round(data.intensity * 100) + '%';

  renderScores(data.all_scores, data.emotion);

  if (showVoice && data.voice_config) {
    renderVoiceConfig(data.voice_config);
    document.getElementById('voiceConfig').style.display = 'block';
  } else {
    document.getElementById('voiceConfig').style.display = 'none';
  }
}

function animateBar(id, pct) {
  const bar = document.getElementById(id);
  bar.style.width = '0%';
  requestAnimationFrame(() => {
    setTimeout(() => { bar.style.width = Math.min(100, pct) + '%'; }, 50);
  });
}

function renderScores(scores, topEmotion) {
  const wrap = document.getElementById('scoresSection');
  if (!scores || Object.keys(scores).length === 0) { wrap.innerHTML = ''; return; }

  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  wrap.innerHTML = sorted.map(([label, score]) => {
    const isTop = label === topEmotion;
    const emoji = EMOTION_EMOJIS[label] || '•';
    return `
      <div class="score-chip ${isTop ? 'top' : ''}">
        <span>${emoji}</span>
        <span class="score-chip-label">${label}</span>
        <span class="score-chip-val">${(score * 100).toFixed(1)}%</span>
      </div>`;
  }).join('');
}

function renderVoiceConfig(vc) {
  const grid = document.getElementById('vcGrid');
  const items = [
    { label: 'Rate', value: vc.rate, sub: 'speech speed' },
    { label: 'Pitch', value: vc.pitch, sub: 'audio pitch' },
    { label: 'Volume', value: vc.volume, sub: 'amplitude' },
  ];
  grid.innerHTML = items.map(item => `
    <div class="vc-item">
      <div class="vc-item-label">${item.label}</div>
      <div class="vc-item-value">${item.value}</div>
      <div class="vc-item-sub">${item.sub}</div>
    </div>
  `).join('');
}

// ── Render audio player ──
function showAudio(url) {
  currentAudioUrl = url;
  const card = document.getElementById('audioCard');
  card.style.display = 'block';

  const player = document.getElementById('audioPlayer');
  player.src = url;
  player.load();

  const dl = document.getElementById('downloadBtn');
  dl.href = url;
  dl.download = url.split('/').pop();
  dl.style.display = 'inline-flex';

  renderWaveform();
  setTimeout(() => player.play().catch(() => {}), 200);
}

function renderWaveform() {
  const container = document.getElementById('waveBars');
  container.innerHTML = '';
  const count = 48;
  for (let i = 0; i < count; i++) {
    const bar = document.createElement('div');
    bar.className = 'wave-bar';
    const height = 20 + Math.random() * 80;
    bar.style.height = height + '%';
    bar.style.animationDelay = (i * 0.025) + 's';
    bar.style.animationDuration = (0.8 + Math.random() * 0.6) + 's';
    container.appendChild(bar);
  }
}

// ── Ambient background canvas ──
(function initCanvas() {
  const canvas = document.getElementById('bgCanvas');
  const ctx = canvas.getContext('2d');
  let particles = [];
  const N = 40;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  for (let i = 0; i < N; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 2 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      hue: Math.random() > 0.5 ? 260 : 190,
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue}, 80%, 70%, 0.6)`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }
  draw();
})();

// ── Utility ──
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}
