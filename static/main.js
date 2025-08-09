const form = document.getElementById('genForm');
const out = document.getElementById('result');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  out.textContent = "Processing... (this can take a moment for large MP3s)";
  const fd = new FormData(form);
  try {
    const r = await fetch('/generate', { method:'POST', body: fd });
    const j = await r.json();
    if (!j.ok) {
      out.textContent = "Error: " + (j.error || "Unknown");
      return;
    }
    out.textContent = JSON.stringify(j, null, 2) + "\n\nDownload: " + location.origin + j.downloadUrl;
  } catch (err) {
    out.textContent = "Network error: " + err.message;
  }
});
