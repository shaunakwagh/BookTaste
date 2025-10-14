import pika
import json
import uuid
from app import app, db, Book
import os

def fetch_book_data_with_rating(query):
    import urllib.request
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

def process_task(ch, method, properties, body):
    data = json.loads(body.decode())
    user_input = data['user_input']
    print(f"Received task for book: {user_input}")

    with app.app_context():
        book_data = fetch_book_data_with_rating(user_input)
        if not book_data or not book_data['title']:
            print(f"No book found for: {user_input}")
            return
        if not book_data.get('isbn'):
            book_data['isbn'] = f"gen-{uuid.uuid4().hex}"
        existing = Book.query.filter_by(title=book_data.get('title')).first()
        if existing:
            print(f"Book already collected: {book_data.get('title')}")
            return
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
        print(f"Saved book title: {new_book.title}")

def main():
    amqp_url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(amqp_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='book_tasks')
    channel.basic_consume(queue='book_tasks', on_message_callback=process_task, auto_ack=True)
    print('Worker is waiting for book tasks...')
    channel.start_consuming()

if __name__ == '__main__':
    main()

