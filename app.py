#!/usr/bin/env python3
from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import uuid
import urllib.request
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
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
    <title>Book Recommendation System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        form { margin: 20px 0; }
        input, button { padding: 10px; margin: 5px; }
        .result { margin: 20px 0; padding: 15px; background-color: #f0f0f0; }
    </style>
</head>
<body>
    <h1>Book Recommendation System</h1>
    <h3>Search and collect book data from Open Library API</h3>
    <form action="/collect" method="POST">
        <label>Enter ISBN (e.g., 9780140328721) or book title:</label><br>
        <input name="user_input" placeholder="ISBN or book title" required>
        <input type="submit" value="Collect Book Data!">
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

def fetch_book_data_with_rating(query):
    search_url = f"https://openlibrary.org/search.json?q={query}&limit=1"
    try:
        with urllib.request.urlopen(search_url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            docs = data.get('docs', [])
            if docs:
                doc = docs[0]
                title = doc.get('title', 'Unknown')
                author = ', '.join(doc.get('author_name', [])) if doc.get('author_name') else None
                isbn = doc['isbn'][0] if doc.get('isbn') else None
                publish_year = doc.get('first_publish_year')
                page_count = doc.get('number_of_pages_median')
                cover_edition_key = doc.get('cover_edition_key')
                work_key = doc.get('key')
                rating = None
                if work_key and work_key.startswith("/works/"):
                    ratings_url = f"https://openlibrary.org{work_key}/ratings.json"
                    try:
                        with urllib.request.urlopen(ratings_url) as rresp:
                            rdata = json.loads(rresp.read().decode('utf-8'))
                            rating = rdata.get('summary', {}).get('average')
                    except Exception as re:
                        print(f"Could not retrieve ratings for {work_key}: {re}")
                return {
                    'title': title,
                    'author': author,
                    'isbn': isbn,
                    'publish_year': publish_year,
                    'page_count': page_count,
                    'cover_edition_key': cover_edition_key,
                    'work_key': work_key,
                    'rating': rating
                }
    except Exception as e:
        print("OpenLibrary fetch error:", e)
    return None

@app.route('/')
def main():
    return render_template_string(HTML_TEMPLATE)

@app.route('/collect', methods=['POST'])
def collect():
    raw_input = request.form.get('user_input', '').strip()
    if not raw_input:
        return "Please enter a book title or ISBN!"
    book_data = fetch_book_data_with_rating(raw_input)
    if not book_data or not book_data['title']:
        return f"No book found for: {raw_input} <br><a href='/'>Go back</a>"
    # If OpenLibrary didn't return an ISBN, generate a synthetic one
    if not book_data.get('isbn'):
        book_data['isbn'] = f"gen-{uuid.uuid4().hex}"

    existing = Book.query.filter_by(title=book_data.get('title')).first()
    if existing:
        return f"Book already collected: {book_data.get('title')} <br><a href='/'>Go back</a>"

    new_book = Book(
        isbn=book_data.get('isbn'),
        title=book_data.get('title'),
        author=book_data.get('author'),
        publish_year=book_data.get('publish_year'),
        page_count=book_data.get('page_count'),
        rating=book_data.get('rating'),
        cover_edition_key=book_data.get('cover_edition_key'),
        work_key=book_data.get('work_key')
    )
    db.session.add(new_book)
    db.session.commit()
    return f"Saved book title: {new_book.title} <br><a href='/'>Go back</a>"

@app.route('/get_taste')
def get_recommendations():
    books = [b for b in Book.query.all() if b.rating is not None]
    if len(books) == 0:
        return "<h3>No books with a rating collected yet.</h3><br><a href='/'>Go back</a>"
    avg_rating = sum(b.rating for b in books) / len(books)
    result_html = f"<h2>Your Reading Taste Score</h2>"
    result_html += f"<p><strong>Average rating of your collected books is:</strong> {avg_rating:.2f} / 5</p>"

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
