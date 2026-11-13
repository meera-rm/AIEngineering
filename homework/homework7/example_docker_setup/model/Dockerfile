FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/models
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY __init__.py app.py service.py ./model/
EXPOSE 8000
CMD ["uvicorn", "model.app:app", "--host", "0.0.0.0", "--port", "8000"]
