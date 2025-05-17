FROM python:3.12-slim

# Install ffmpeg and build dependencies
RUN apt-get update && apt-get install -y ffmpeg build-essential python3-dev libffi-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
