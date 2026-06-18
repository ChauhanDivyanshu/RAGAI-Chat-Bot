FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    poppler-utils \
    ghostscript \
    libmagic1 \
    libmagic-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs models_cache tmp

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
