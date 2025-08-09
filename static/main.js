const form = document.getElementById('genForm');
const out = document.getElementById('result');
const MAX_MB = 25;
const ALLOWED_XML = ['text/xml', 'application/xml'];
const ALLOWED_AUDIO = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/aac', 'audio/m4a', 'audio/mp4'];

function showError(msg) {
  out.style.color = 'red';
  out.textContent = 'Error: ' + msg;
}

function showMessage(msg) {
  out.style.color = '';
  out.textContent = msg;
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
  const fd = new FormData(form);
  try {
    const r = await fetch('/generate', { method: 'POST', body: fd });
    const j = await r.json();
    if (!j.ok) {
      showError(j.error || 'Unknown');
      return;
    }
    showMessage(JSON.stringify(j, null, 2) + "\n\nDownload: " + location.origin + j.downloadUrl);
  } catch (err) {
    showError('Network error: ' + err.message);
  }
});
