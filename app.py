#!/usr/bin/env python3
from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os

app = Flask(__name__)
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    db_url = 'sqlite:///:memory:' 
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Text)
    title = db.Column(db.Text)
    author = db.Column(db.Text)
    publish_year = db.Column(db.Integer)
    page_count = db.Column(db.Integer)
    rating = db.Column(db.Float)
    cover_edition_key = db.Column(db.Text)
    work_key = db.Column(db.Text)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        form { margin: 20px 0; }
        input, button { padding: 10px; margin: 5px; }
        .result { margin: 20px 0; padding: 15px; background-color: #f0f0f0; }
    </style>
</head>
<body>
    <h1>Book Taste System</h1>
    <h3>Search and collect book data from Open Library API (queued)</h3>
    <form action="/collect" method="POST">
        <label>Enter ISBN (e.g., 9780140328721) or book title:</label><br>
        <input name="user_input" placeholder="ISBN or book title" required>
        <input type="submit" value="Queue Book Data!">
    </form>
    <h3>See how good is your Book taste!</h3>
    <form action="/get_taste" method="GET">
        <button type="submit">How good is your Book taste!</button>
    </form>
    <h3>View all collected books</h3>
    <form action="/view_books" method="GET">
        <button type="submit">View All Books</button>
    </form>
</body>
</html>
"""

def send_to_queue(user_input):
    amqp_url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(amqp_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='book_tasks')
    task = json.dumps({"user_input": user_input})
    channel.basic_publish(exchange='', routing_key='book_tasks', body=task)
    connection.close()

@app.route('/')
def main():
    return render_template_string(HTML_TEMPLATE)

@app.route('/collect', methods=['POST'])
def collect():
    raw_input = request.form.get('user_input', '').strip()
    if not raw_input:
        return "Please enter a book title or ISBN!"
    send_to_queue(raw_input)
    return f"Task queued for: {raw_input} <br><a href='/'>Go back</a>"

@app.route('/get_taste')
def get_recommendations():
    books = [b for b in Book.query.all() if b.rating is not None]
    if len(books) == 0:
        return "<h3>No books with a rating collected yet.</h3><br><a href='/'>Go back</a>"
    avg_rating = sum(b.rating for b in books) / len(books)
    result_html = f"<h2>Your Reading Taste Score</h2>"
    result_html += f"<p><strong>Average rating of your taste:</strong> {avg_rating:.2f} / 5</p>"
    result_html += "<h3>Here are your rated books:</h3>"
    for i, book in enumerate(books, 1):
        cover_html = ""
        if book.cover_edition_key:
            cover_html = f"<img src='https://covers.openlibrary.org/b/olid/{book.cover_edition_key}-M.jpg' alt='cover' style='height:120px;'><br>"
        result_html += f"""
        <div class='result'>
            {cover_html}
            <h3>{i}. {book.title}</h3>
            <p><strong>Author:</strong> {book.author or 'Unknown'}</p>
            <p><strong>ISBN:</strong> {book.isbn or 'Unknown'}</p>
            <p><strong>Published:</strong> {book.publish_year or 'Unknown'}</p>
            <p><strong>Pages:</strong> {book.page_count or 'Unknown'}</p>
            <p><strong>Rating:</strong> {book.rating if book.rating is not None else 'Unknown'}</p>
            <p><strong>Work Key:</strong> {book.work_key or 'Unknown'}</p>
            <p><strong>Cover Edition Key:</strong> {book.cover_edition_key or 'Unknown'}</p>
        </div>
        """
    result_html += "<br><a href='/'>Go back</a>"
    return result_html

@app.route('/view_books')
def view_books():
    books = Book.query.all()
    result_html = f"<h2>Collected Books ({len(books)} total):</h2>"
    for book in books:
        cover_html = ""
        if book.cover_edition_key:
            cover_html = f"<img src='https://covers.openlibrary.org/b/olid/{book.cover_edition_key}-M.jpg' alt='cover' style='height:120px;'><br>"
        result_html += f"""
        <div class='result'>
            {cover_html}
            <h3>{book.title}</h3>
            <p><strong>Author:</strong> {book.author or 'Unknown'}</p>
            <p><strong>ISBN:</strong> {book.isbn or 'Unknown'}</p>
            <p><strong>Published:</strong> {book.publish_year or 'Unknown'}</p>
            <p><strong>Pages:</strong> {book.page_count or 'Unknown'}</p>
            <p><strong>Rating:</strong> {book.rating if book.rating is not None else 'Unknown'}</p>
            <p><strong>Work Key:</strong> {book.work_key or 'Unknown'}</p>
            <p><strong>Cover Edition Key:</strong> {book.cover_edition_key or 'Unknown'}</p>
        </div>
        """
    if not books:
        result_html += "<p>No books collected yet. Start by searching for some books!</p>"
    result_html += "<br><a href='/'>Go back</a>"
    return result_html

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
