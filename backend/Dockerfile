FROM python:3.11-slim

# set working dir
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# copy project
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

ENV FLASK_APP=app.py

CMD ["./start.sh"]
