"""JSON formatter for project/monitor application logs (SDK/uvicorn logs may differ)."""
import json
import logging
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        doc = {'timestamp': datetime.now(timezone.utc).isoformat(), 'level': record.levelname,
               'logger': record.name, 'event': record.getMessage()}
        if record.exc_info:
            doc['exception'] = self.formatException(record.exc_info)
        return json.dumps(doc, ensure_ascii=False)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
