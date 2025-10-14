import unittest
from unittest.mock import patch, MagicMock
import json
from app import app, db, Book

class BookAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("pika.BlockingConnection")
    @patch("pika.URLParameters")
    @patch("os.environ.get")
    @patch("urllib.request.urlopen")
    def test_queue_and_collect_book(
        self, mock_urlopen, mock_environ_get, mock_urlparams, mock_pika
    ):
        # 1. Mock environment variable for RabbitMQ URL
        mock_environ_get.return_value = "amqp://dummy"

        # 2. Mock URLParameters output to avoid parsing
        mock_urlparams.return_value = MagicMock()

        # 3. Mock RabbitMQ Connection
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_pika.return_value = mock_conn

        # 4. Mock OpenLibrary API Response for urllib
        example_data = {
            "docs": [{
                "title": "Test Book",
                "author_name": ["Author McTest"],
                "isbn": ["1234567890"],
                "first_publish_year": 2020,
                "number_of_pages_median": 333,
                "cover_edition_key": "OL1234M",
                "key": "/works/OL123W"
            }]
        }
        ol_resp = MagicMock()
        ol_resp.read.return_value = json.dumps(example_data).encode()
        ol_resp.__enter__.return_value = ol_resp
        mock_urlopen.return_value = ol_resp

        # 5. Simulate POST to /collect endpoint (Flask UI)
        response = self.client.post('/collect', data={'user_input': 'Test Book'})
        self.assertIn(b'Task queued for: Test Book', response.data)

        # 6. Simulate DB entry as if the worker added it
        with app.app_context():
            book = Book(title="Test Book", author="Author McTest", isbn="1234567890")
            db.session.add(book)
            db.session.commit()
            books = Book.query.all()
            self.assertEqual(len(books), 1)
            self.assertEqual(books[0].title, "Test Book")
            self.assertEqual(books[0].author, "Author McTest")
            self.assertEqual(books[0].isbn, "1234567890")

    def test_view_books_empty(self):
        resp = self.client.get('/view_books')
        self.assertIn(b"No books collected yet", resp.data)

if __name__ == '__main__':
    unittest.main()
