FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
EXPOSE 7860

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]