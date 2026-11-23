FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
# 1 Worker, da Jobs im Speicher gehalten werden; Threads für parallele Downloads
CMD gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT --timeout 600 app:app
