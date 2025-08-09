FROM python:3.11-slim
WORKDIR /app
# System deps for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=app.py FLASK_ENV=production PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python","app.py"]
