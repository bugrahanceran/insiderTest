# Hafif bir Python imajı kullanıyoruz
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Önce requirements kopyala ve kur (Docker layer caching avantajı için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kaynak kodları kopyala
COPY src/ ./src/

# Environment variable defaults
ENV PYTHONPATH=/app/src

# Container başladığında çalışacak komut
# -v: Verbose (detaylı çıktı)
# -s: Print statement'ları konsola bas
CMD ["pytest", "-v", "-s", "src/tests/"]