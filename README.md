# xLights Sequence Generator

This project provides a simple Flask-based web service that analyzes an audio file and an xLights rgbeffects XML to help build light sequences. It extracts tempo information and basic model details to assist in generating sequences.

## Features
- Upload an xLights `rgbeffects.xml` file and a matching audio track.
- Automatic BPM detection and beat timing extraction using `librosa`.
- Basic model parsing from the XML to report model names and sizes.

## Installation

Install system dependencies for audio processing (FFmpeg and libsndfile) and Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the development server:

```bash
python app.py
```

The application listens on `http://localhost:5000` and provides a simple upload form.

### Docker

A `Dockerfile` and `docker-compose.yml` are provided for containerized deployment:

```bash
# Build and run locally
Dockerfile:
  docker build -t xlights-seq .
  docker run -p 5000:5000 xlights-seq

# Or with docker compose
  docker-compose up --build
```

Uploaded files are stored under `uploads/` and generated data in `generated/`.

## Endpoints
- `GET /` – Serve the upload form.
- `POST /generate` – Accepts `xml` and `audio` files, returning JSON with beat timings and model information.

## Notes
This repository currently focuses on file handling and beat analysis. Sequence generation is a placeholder for future development.
