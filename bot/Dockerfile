FROM python:3.12-slim

WORKDIR /bot

# Installer la librairie système zbar pour pyzbar et nettoyer le cache apt
RUN apt-get update && apt-get install -y libzbar0 && rm -rf /var/lib/apt/lists/*

COPY . /bot

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"] 