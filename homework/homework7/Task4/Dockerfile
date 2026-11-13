FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 WORKFLOW_LOG_PATH=/app/logs/workflow_trace.jsonl
WORKDIR /app
COPY requirements-workflow.txt .
RUN pip install --no-cache-dir -r requirements-workflow.txt
COPY workflow.py workflow_api.py service_clients.py llm_service.py trace_logger.py ./
RUN mkdir -p /app/logs
EXPOSE 8000
CMD ["uvicorn", "workflow_api:app", "--host", "0.0.0.0", "--port", "8000"]
