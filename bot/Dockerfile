FROM python:3.12-slim

WORKDIR /app

# Installer la librairie système zbar pour pyzbar
RUN apt-get update && apt-get install -y libzbar0

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"] 