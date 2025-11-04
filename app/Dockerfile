FROM python:3.13-slim

WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

COPY requirements.txt ./app/requirements.txt
COPY data.json ./app/data.json
RUN pip install --no-cache-dir -r app/requirements.txt

COPY . ./app

CMD ["python", "-m", "app.app"]
