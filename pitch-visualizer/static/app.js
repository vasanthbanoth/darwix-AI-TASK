// app.js — Pitch Visualizer Frontend

let selectedStyle = document.querySelector('.style-pill.active')?.dataset?.style || 'cinematic';
let panelCount = 0;
let totalPanels = 0;
let evtSource = null;
let panelData = [];

// Character counter
const storyInput = document.getElementById('storyInput');
storyInput.addEventListener('input', () => {
  document.getElementById('charCount').textContent = storyInput.value.length;
});

function selectStyle(btn) {
  document.querySelectorAll('.style-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  selectedStyle = btn.dataset.style;
}

function fillExample(card) {
  storyInput.value = card.querySelector('.ex-preview').textContent;
  document.getElementById('charCount').textContent = storyInput.value.length;
  storyInput.scrollIntoView({ behavior: 'smooth' });
}

async function generate() {
  const text = storyInput.value.trim();
  if (!text) { alert('Please enter your story text first.'); return; }

  // Reset UI
  panelCount = 0; totalPanels = 0; panelData = [];
  document.getElementById('storyboardGrid').innerHTML = '';
  document.getElementById('storyboardSection').style.display = 'none';
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressLabel').textContent = 'Segmenting narrative…';
  document.getElementById('progressCount').textContent = '';

  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  document.getElementById('btnIcon').textContent = '⏳';
  document.getElementById('btnText').textContent = 'Generating…';

  if (evtSource) { evtSource.close(); evtSource = null; }

  try {
    // Make POST request and get SSE readable stream
    const response = await fetch('/pitch-visualizer/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, style: selectedStyle }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Generation failed.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          handleSSEEvent(JSON.parse(line.slice(6)));
        }
      }
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
    resetBtn();
    document.getElementById('progressWrap').style.display = 'none';
  }
}

function handleSSEEvent(evt) {
  switch (evt.type) {
    case 'start':
      document.getElementById('progressLabel').textContent = 'Segmenting narrative…';
      break;

    case 'total':
      totalPanels = evt.total;
      document.getElementById('progressCount').textContent = `0 / ${totalPanels}`;
      document.getElementById('storyboardSection').style.display = 'block';
      break;

    case 'processing':
      document.getElementById('progressLabel').textContent =
        `Generating panel ${evt.index + 1}…`;
      addPanelPlaceholder(evt.index, evt.scene);
      break;

    case 'panel':
      panelCount++;
      updatePanel(evt.index, evt);
      updateProgress(panelCount, totalPanels);
      panelData.push(evt);
      break;

    case 'done':
      document.getElementById('progressLabel').textContent = '✅ Storyboard complete!';
      updateProgress(totalPanels, totalPanels);
      resetBtn();
      break;

    case 'error':
      alert(`Server error: ${evt.message}`);
      resetBtn();
      break;
  }
}

function updateProgress(done, total) {
  const pct = total > 0 ? (done / total) * 100 : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressCount').textContent = `${done} / ${total}`;
}

function addPanelPlaceholder(idx, scene) {
  const grid = document.getElementById('storyboardGrid');
  const card = document.createElement('div');
  card.className = 'panel-card';
  card.id = `panel-${idx}`;
  card.style.animationDelay = (idx * 0.08) + 's';
  card.innerHTML = `
    <div class="panel-img-wrap">
      <span class="panel-number">PANEL ${idx + 1}</span>
      <div class="panel-loading" id="panel-loading-${idx}">
        <div class="panel-spinner"></div>
        <div class="panel-loading-text">Generating…</div>
      </div>
    </div>
    <div class="panel-body">
      <p class="panel-caption">${escapeHtml(scene)}</p>
    </div>
  `;
  grid.appendChild(card);
}

function updatePanel(idx, data) {
  const loadingEl = document.getElementById(`panel-loading-${idx}`);
  if (!loadingEl) return;

  const imgWrap = loadingEl.parentElement;
  if (data.image_url) {
    const img = document.createElement('img');
    img.src = data.image_url;
    img.alt = `Storyboard panel ${idx + 1}`;
    img.loading = 'lazy';
    imgWrap.replaceChild(img, loadingEl);

    // Keep panel number overlay
    const num = imgWrap.querySelector('.panel-number');
    if (!num) {
      const numEl = document.createElement('span');
      numEl.className = 'panel-number';
      numEl.textContent = `PANEL ${idx + 1}`;
      imgWrap.appendChild(numEl);
    }
  } else {
    loadingEl.innerHTML = `<div style="color:#ff6b6b;font-size:12px;padding:12px">⚠️ Image unavailable</div>`;
  }

  // Add AI prompt toggle
  const card = document.getElementById(`panel-${idx}`);
  const body = card.querySelector('.panel-body');
  const promptDiv = document.createElement('div');
  promptDiv.innerHTML = `
    <div class="panel-prompt-toggle" onclick="togglePrompt(this)">▼ See AI prompt</div>
    <div class="panel-prompt-text">${escapeHtml(data.prompt || '')}</div>
  `;
  body.appendChild(promptDiv);
}

function togglePrompt(el) {
  const next = el.nextElementSibling;
  next.classList.toggle('visible');
  el.textContent = next.classList.contains('visible') ? '▲ Hide AI prompt' : '▼ See AI prompt';
}

function resetBtn() {
  const btn = document.getElementById('generateBtn');
  btn.disabled = false;
  document.getElementById('btnIcon').textContent = '🎬';
  document.getElementById('btnText').textContent = 'Generate Storyboard';
}

function exportHTML() {
  const panels = Array.from(document.querySelectorAll('.panel-card'));
  let html = `<!DOCTYPE html><html><head><title>Storyboard Export</title>
<style>
body{font-family:sans-serif;background:#0a0a0a;color:#eee;padding:30px;max-width:1100px;margin:auto;}
h1{font-size:22px;margin-bottom:24px;color:#F5C842;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px;}
.panel{background:#111;border-radius:12px;overflow:hidden;border:1px solid #222;}
.panel img{width:100%;aspect-ratio:3/2;object-fit:cover;}
.panel-cap{padding:12px;font-size:13px;color:#aaa;line-height:1.5;}
.panel-num{font-size:11px;color:#F5C842;font-weight:700;margin-bottom:4px;}
</style></head><body>
<h1>🎬 AI Generated Storyboard</h1><div class="grid">`;

  panelData.forEach((p, i) => {
    const imgSrc = p.image_url ? `http://localhost:8001${p.image_url}` : '';
    html += `<div class="panel">
      ${imgSrc ? `<img src="${imgSrc}" alt="Panel ${i+1}" />` : '<div style="height:180px;background:#1a1a2e;display:flex;align-items:center;justify-content:center;color:#555;">No image</div>'}
      <div class="panel-cap"><div class="panel-num">PANEL ${i+1}</div>${escapeHtml(p.scene)}</div>
    </div>`;
  });
  html += `</div></body></html>`;

  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'storyboard.html';
  a.click();
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Ambient canvas
(function() {
  const canvas = document.getElementById('bgCanvas');
  const ctx = canvas.getContext('2d');
  function resize() { canvas.width = innerWidth; canvas.height = innerHeight; }
  window.addEventListener('resize', resize); resize();
  const pts = Array.from({length:35}, () => ({
    x: Math.random()*innerWidth, y: Math.random()*innerHeight,
    vx:(Math.random()-0.5)*0.25, vy:(Math.random()-0.5)*0.25,
    hue: Math.random()>0.5?50:180,
  }));
  (function tick() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    pts.forEach(p => {
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0)p.x=canvas.width; if(p.x>canvas.width)p.x=0;
      if(p.y<0)p.y=canvas.height; if(p.y>canvas.height)p.y=0;
      ctx.beginPath(); ctx.arc(p.x,p.y,1.5,0,Math.PI*2);
      ctx.fillStyle=`hsla(${p.hue},80%,70%,0.7)`; ctx.fill();
    });
    requestAnimationFrame(tick);
  })();
})();
