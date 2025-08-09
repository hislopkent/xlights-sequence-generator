const form = document.getElementById('genForm');
const out = document.getElementById('result');
const spinner = document.getElementById('spinner');
const previewCanvas = document.getElementById('previewCanvas');
const MAX_MB = 25;
const ALLOWED_XML = ['text/xml', 'application/xml'];
const ALLOWED_AUDIO = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/aac', 'audio/m4a', 'audio/mp4'];

function showError(msg) {
  out.className = 'error-banner';
  out.textContent = msg;
}

function showMessage(msg) {
  out.className = '';
  out.textContent = msg;
}

function showResult(j) {
  const minutes = Math.floor(j.durationMs / 60000);
  const seconds = Math.floor((j.durationMs % 60000) / 1000)
    .toString()
    .padStart(2, '0');
  const models = j.modelNames || [];
  const firstTen = models.slice(0, 10);
  let modelText = firstTen.join(', ');
  if (models.length > 10) {
    modelText += ` +${models.length - 10} more`;
  }
  const downloadUrl = location.origin + j.downloadUrl;
  out.className = 'result-panel';
  out.innerHTML = `
      <p><strong>Detected BPM:</strong> ${j.bpm ?? 'n/a'}</p>
      <p><strong>Manual BPM:</strong> ${j.manualBpm ?? 'n/a'}</p>
      <p><strong>Duration:</strong> ${minutes}:${seconds}</p>
      <p><strong>Models (${j.modelCount}):</strong> ${modelText}</p>
      <a class="download-btn" href="${downloadUrl}">Download</a>
    `;
    renderPreview(j.jobId, j.durationMs);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const layoutFile = form.layout.files[0];
  const audioFile = form.audio.files[0];
  const maxBytes = MAX_MB * 1024 * 1024;

  if (layoutFile.size > maxBytes || audioFile.size > maxBytes) {
    showError(`Files must be smaller than ${MAX_MB}MB.`);
    return;
  }
  if (!ALLOWED_XML.includes(layoutFile.type)) {
    showError('Unsupported layout file type.');
    return;
  }
  if (!ALLOWED_AUDIO.includes(audioFile.type)) {
    showError('Unsupported audio file type.');
    return;
  }

  showMessage('Processing... (this can take a moment for large MP3s)');
  spinner.style.display = 'block';
  const fd = new FormData(form);
  try {
    const r = await fetch('/generate', { method: 'POST', body: fd });
    const j = await r.json();
    if (!j.ok) {
      showError(j.error || 'Unknown');
      return;
    }
    showResult(j);
  } catch (err) {
    showError('Network error: ' + err.message);
  } finally {
    spinner.style.display = 'none';
  }
});

// Initial message
  showMessage('Waiting...');

async function renderPreview(jobId, durationMs) {
  if (!previewCanvas) return;
  try {
    const r = await fetch(`/preview.json?job=${encodeURIComponent(jobId)}`);
    const data = await r.json();
    if (!data.ok) return;
    const width = previewCanvas.width;
    const height = previewCanvas.height;
    const ctx = previewCanvas.getContext('2d');
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = '#bbb';
    ctx.lineWidth = 1;
    (data.beatTimes || []).forEach(t => {
      const x = (t * 1000 / durationMs) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    });
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 3;
    (data.sections || []).forEach(s => {
      const x = (s.time * 1000 / durationMs) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    });
    previewCanvas.style.display = 'block';
  } catch (err) {
    // ignore errors
  }
}
