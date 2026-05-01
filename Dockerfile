FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render uses PORT env var, but we hardcoded 10000 or can use the env
CMD ["python", "src/app.py"]
