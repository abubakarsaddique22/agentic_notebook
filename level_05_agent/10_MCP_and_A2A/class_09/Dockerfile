FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY --chown=appuser:appuser . /app
RUN mkdir -p /app/data/index_storage /app/state && chown -R appuser:appuser /app/data/index_storage /app/state
USER appuser
CMD ["python", "servers/travel_server.py"]
