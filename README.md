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
