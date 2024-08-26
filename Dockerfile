
FROM python:3.9-slim

RUN apt-get update

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
EXPOSE 7860

CMD uvicorn main:app --host 0.0.0.0 --port 8080
