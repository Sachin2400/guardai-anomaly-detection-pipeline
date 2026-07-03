FROM python:3.10-slim

WORKDIR /app

# System deps needed by scikit-learn / spacy wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY src/ ./src/
COPY data/ ./data/

# Train the anomaly model at build time so the image is ready to serve
RUN python src/data_generation.py && python src/anomaly_engine.py

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
