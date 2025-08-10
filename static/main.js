const form = document.getElementById('genForm');
const out = document.getElementById('result');
const spinner = document.getElementById('spinner');
const previewCanvas = document.getElementById('previewCanvas');
const MAX_MB = 25;
const ALLOWED_XML = ['text/xml', 'application/xml'];
const ALLOWED_AUDIO = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/aac', 'audio/m4a', 'audio/mp4'];
const EXPORT_FORMAT_LABELS = {
  rgbeffects_xml: 'xlights_rgbeffects.xml',
  xsq: 'XSQ (single file)',
  xsqz: 'XSQZ (zip package)'
};

function showError(msg) {
  out.className = 'error-banner';
  out.textContent = msg;
}

function showMessage(msg) {
  out.className = '';
  out.textContent = msg;
}

function showResult(j) {
  out.className = 'result-panel';
  const durationSec = j.durationMs ? (j.durationMs / 1000).toFixed(2) : 'unknown';
  const selCount = j.selectedModelCount ?? j.modelCount ?? 0;
  const totalCount = j.totalModelCount ?? selCount;
  out.innerHTML = `
    <div><b>Export:</b> ${j.exportFormat}</div>
    <div><b>BPM (auto):</b> ${j.bpm ?? "unknown"} · v${j.version ?? "unknown"}</div>
    <div><b>Duration:</b> ${durationSec}s</div>
    <div><b>Counts:</b> beats ${j.beatCount} · downbeats ${j.downbeatCount} · sections ${j.sectionCount}</div>
    <div><b>Models:</b> ${selCount} / ${totalCount}</div>
    <p><a href="${j.downloadUrl}" download>Download file</a></p>
  `;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const layoutFile = form.layout.files[0];
  const audioFile = form.audio.files[0];
  const networksFile = form.networks.files[0];
  const maxBytes = MAX_MB * 1024 * 1024;

  if (layoutFile.size > maxBytes || audioFile.size > maxBytes || (networksFile && networksFile.size > maxBytes)) {
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
  if (networksFile && !ALLOWED_XML.includes(networksFile.type)) {
    showError('Unsupported networks file type.');
    return;
  }

  showMessage('Processing... (this can take a moment for large MP3s)');
  spinner.style.display = 'block';
  const fd = new FormData(form);
  try {
    const r = await fetch('/generate', { method: 'POST', body: fd });
    const j = await r.json();
    if (!j.ok) {
      showError(j.error);
      return;
    }
    showResult(j);
    renderPreview(j.jobId, j.durationMs);
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

const modelTree = document.getElementById('modelTree');
const searchBox = document.getElementById('searchBox');
const showGroups = document.getElementById('showGroups');
const showModels = document.getElementById('showModels');
const layoutInput = document.querySelector('input[name="layout"]');

let layoutTree = null;

function renderTree(node, depth = 0) {
  const vis =
    (node.type === 'group' && showGroups.checked) ||
    (node.type === 'model' && showModels.checked) ||
    node.name === 'ROOT';
  if (!vis) return '';
  const match = (searchBox.value || '').toLowerCase();
  const visibleName = node.name.toLowerCase().includes(match);
  const badge =
    node.type === 'model'
      ? ` <small>(${node.strings ?? '?'} strings, ${node.nodes ?? '?'} nodes)</small>`
      : '';
  const kids = (node.children || [])
    .map((c) => renderTree(c, depth + 1))
    .join('');
  const hasKids = !!kids;
  const row = `<div data-type="${node.type}" style="margin-left:${depth * 16}px">
    ${hasKids ? '▸' : ''} <strong>${node.name}</strong> <em>${node.type}</em>${badge}
  </div>`;
  return visibleName || kids ? row + kids : '';
}

async function inspectLayout(file) {
  const fd = new FormData();
  fd.append('layout', file);
  const r = await fetch('/inspect-layout', { method: 'POST', body: fd });
  const j = await r.json();
  if (!j.ok) {
    modelTree.textContent = 'Failed to parse layout: ' + (j.error || '');
    return;
  }
  layoutTree = j.tree;
  modelTree.innerHTML = renderTree(layoutTree);
}

layoutInput?.addEventListener('change', () => {
  if (layoutInput.files?.[0]) inspectLayout(layoutInput.files[0]);
});
[searchBox, showGroups, showModels].forEach((el) =>
  el?.addEventListener('input', () => {
    if (layoutTree) modelTree.innerHTML = renderTree(layoutTree);
  })
);
