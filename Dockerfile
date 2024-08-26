FROM python:3.9-slim

RUN apt-get update && apt-get install -y nginx

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/jetrr-sajeel-haider-1-029d48a46f5f.json"

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8080

CMD service nginx start && uvicorn main:app --host 0.0.0.0 --port 8080
