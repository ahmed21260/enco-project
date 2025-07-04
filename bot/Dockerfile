FROM python:3.12-slim

WORKDIR /bot

# Installer la librairie système zbar pour pyzbar
RUN apt-get update && apt-get install -y libzbar0

COPY ./bot /bot

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"] 