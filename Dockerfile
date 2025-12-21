FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src

# -v: Verbose mode
# -s: Print statement'ları konsola bas
CMD ["pytest", "-v", "-s", "src/tests/"]