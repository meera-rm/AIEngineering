FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/hf-cache
WORKDIR /app
COPY requirements-retrieval.txt .
RUN pip install --no-cache-dir -r requirements-retrieval.txt
# Bake the pinned embedding model into the image (HF_HOME is the runtime cache too).
COPY VectorStore.py download_model.py ./
RUN python download_model.py
COPY retrieval_service.py retrieval_api.py ./
COPY homework5_vector_store ./homework5_vector_store
EXPOSE 8000
CMD ["uvicorn", "retrieval_api:app", "--host", "0.0.0.0", "--port", "8000"]
