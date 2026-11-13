FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-router.txt .
RUN pip install --no-cache-dir -r requirements-router.txt
# Keep the module names the classifier was saved under: ticket_router.TicketRouter
COPY ticket_router.py routing_service.py router_api.py ./
COPY ticket_router.joblib ./
EXPOSE 8000
CMD ["uvicorn", "router_api:app", "--host", "0.0.0.0", "--port", "8000"]
