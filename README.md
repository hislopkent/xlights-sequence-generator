# xLights Sequence Generator (Docker + Watchtower)

Runs a Flask web UI on **port 5000**. Auto-updates via **Watchtower** using the Docker Hub image:
`hislopkent/xlights-sequence-generator:latest`

## Quick Start (Windows 10 + Docker Desktop)
```powershell
docker compose up -d
# then open http://localhost:5000
```

Uploads and outputs are mounted to local folders (`uploads/`, `generated/`).

## Auto-Update Flow
GitHub → build & push image to Docker Hub → Watchtower pulls → container restarts.
This repo includes a GitHub Action to push `:latest`.

### Set Repo Secrets (GitHub → Settings → Secrets → Actions)
- `DOCKERHUB_USERNAME` = hislopkent
- `DOCKERHUB_TOKEN` = <Docker Hub access token>

## Local Development (optional)
Switch compose to build locally instead of pulling from Docker Hub:
```yaml
# in docker-compose.yml, replace the service with:
xlights-seq:
  build: .
  ports: ["5000:5000"]
  volumes:
    - ./uploads:/app/uploads
    - ./generated:/app/generated
  restart: unless-stopped
  labels:
    - "com.centurylinklabs.watchtower.enable=true"
```
Then:
```powershell
docker compose up --build -d
```

## Notes
- Dockerfile includes `ffmpeg` + `libsndfile1` for audio analysis (librosa).
- Health endpoint: `GET /health` → `{ "ok": true }`
- Version endpoint: `GET /version` → `{ "version": "<value>" }`
- Set `APP_VERSION` environment variable to have the web UI display the current version (defaults to `dev`).

## AI Director (optional)
When enabled, `/generate` asks Claude to plan the sequence — which layout group gets
which effect and when — based on the song's tempo/section structure and your house
style, instead of the deterministic default kit.

- Opt in per-request: check **Use AI Director** in the UI (or pass `use_ai=true` to
  `/generate`), optionally with a `style_prompt` describing the mood/colors you want.
- Requires an `ANTHROPIC_API_KEY` environment variable. Without one — or if the API
  call fails or times out, or `OFFLINE=1` — generation falls back automatically to
  the deterministic planner, and the response reports `aiUsed: false` with
  `aiFallbackReason` set.
- `OFFLINE` defaults to `1` (AI calls disabled). Set `OFFLINE=0` and provide
  `ANTHROPIC_API_KEY` to enable it.
- The AI only ever picks from a fixed effect/param whitelist
  (`xlights_seq/effects_catalog.py`); its output is validated before being rendered,
  so a bad or unexpected response can't produce an invalid sequence file.
