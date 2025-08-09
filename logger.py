import logging
import json
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "time": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Include any custom attributes added via "extra"
        for key, value in record.__dict__.items():
            if key in {
                "path",
                "ip",
                "status",
                "duration_ms",
                "error",
                "layout_bytes",
                "audio_bytes",
                "bpm",
            }:
                log[key] = value
        return json.dumps(log)


def get_json_logger(log_file: str) -> logging.Logger:
    """Create a logger that writes JSON lines to the given file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    handler = logging.FileHandler(log_file)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
