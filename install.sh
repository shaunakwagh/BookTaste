#!/bin/bash
sqlite3 books.db << 'EOF'
PRAGMA database_list;
CREATE TABLE IF NOT EXISTS books (
    isbn TEXT NOT NULL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publish_year INTEGER,
    page_count INTEGER,
    rating REAL
);
EOF

echo "Database and table created successfully!"

pip install flask flask-sqlalchemy pika requests flask-testing

echo "Starting worker in background..."
python3 worker.py > worker.log 2>&1 &

echo "Starting Flask application..."
gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:5000
