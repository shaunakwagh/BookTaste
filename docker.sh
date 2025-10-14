#!/bin/bash

docker pull rabbitmq:management
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

sleep 10

cat > Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install flask flask-sqlalchemy pika requests flask-testing gunicorn eventlet
RUN sqlite3 books.db "CREATE TABLE IF NOT EXISTS books (isbn TEXT NOT NULL PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL, publish_year INTEGER, page_count INTEGER, rating REAL);"
EXPOSE 5000
CMD ["bash", "-c", "python3 worker.py > worker.log 2>&1 & gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:5000"]
EOF

docker build -t book-recommendation-project .
docker run -d --name book-recommendation-project --network host -v $(pwd):/app book-recommendation-project

echo "RabbitMQ Management UI: http://localhost:15672 (guest/guest)"
echo "Flask Application: http://localhost:5000"
