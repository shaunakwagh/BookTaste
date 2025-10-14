import unittest
from unittest.mock import patch, MagicMock
import json
from app import app, db, Book

class BookAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def mock_book_urlopen(self, title, author, isbn, key, rating, cover=None, publish_year=None, pages=None):
        search_data = {
            "docs": [{
                "title": title,
                "author_name": [author] if author else [],
                "isbn": [isbn] if isbn else [],
                "key": key,
                "cover_edition_key": cover,
                "first_publish_year": publish_year,
                "number_of_pages_median": pages
            }]
        }
        ratings_data = {"summary": {"average": rating}}
        search_resp = MagicMock()
        search_resp.read.return_value = json.dumps(search_data).encode('utf-8')
        search_resp.__enter__.return_value = search_resp

        ratings_resp = MagicMock()
        ratings_resp.read.return_value = json.dumps(ratings_data).encode('utf-8')
        ratings_resp.__enter__.return_value = ratings_resp

        return [search_resp, ratings_resp]

    @patch('urllib.request.urlopen')
    def test_collect_little_beaver(self, mock_urlopen):
        # Little Beaver and the echo (Open Library OL2211830M)
        mock_urlopen.side_effect = self.mock_book_urlopen(
            title="Little Beaver and the echo",
            author="Amy MacDonald",
            isbn="0399222030",
            key="/works/OL16243773W",
            rating=4.1,
            cover="OL2211830M",
            publish_year=1990,
            pages=32
        )
        resp = self.client.post('/collect', data={'user_input':'Little Beaver and the echo'})
        self.assertIn(b'Saved book title: Little Beaver and the echo', resp.data)
        with app.app_context():
            b = Book.query.filter_by(title='Little Beaver and the echo').first()
            self.assertIsNotNone(b)
            self.assertEqual(b.author, 'Amy MacDonald')
            self.assertEqual(b.isbn, '0399222030')
            self.assertEqual(b.publish_year, 1990)
            self.assertEqual(b.page_count, 32)
            self.assertEqual(b.cover_edition_key, 'OL2211830M')
            self.assertAlmostEqual(b.rating, 4.1, places=2)

    @patch('urllib.request.urlopen')
    def test_collect_swan_song(self, mock_urlopen):
        # Swan Song (Open Library OL24940068M)
        mock_urlopen.side_effect = self.mock_book_urlopen(
            title="Swan Song",
            author="Robert R. McCammon",
            isbn="1501131427",
            key="/works/OL82696W",
            rating=4.4,
            cover="OL24940068M",
            publish_year=2016,
            pages=956
        )
        resp = self.client.post('/collect', data={'user_input':'Swan Song'})
        self.assertIn(b'Saved book title: Swan Song', resp.data)
        with app.app_context():
            b = Book.query.filter_by(title='Swan Song').first()
            self.assertIsNotNone(b)
            self.assertEqual(b.author, 'Robert R. McCammon')
            self.assertEqual(b.isbn, '1501131427')
            self.assertEqual(b.publish_year, 2016)
            self.assertEqual(b.page_count, 956)
            self.assertEqual(b.cover_edition_key, 'OL24940068M')
            self.assertAlmostEqual(b.rating, 4.4, places=2)

    @patch('urllib.request.urlopen')
    def test_collect_harry_potter(self, mock_urlopen):
        # Harry Potter and the Order of the Phoenix (works/OL82548W, edition OL26486989M)
        mock_urlopen.side_effect = self.mock_book_urlopen(
            title="Harry Potter and the Order of the Phoenix",
            author="J.K. Rowling",
            isbn="0439358078",
            key="/works/OL82548W",
            rating=4.5,
            cover="OL26486989M",
            publish_year=2003,
            pages=870
        )
        resp = self.client.post('/collect', data={'user_input':'Harry Potter and the Order of the Phoenix'})
        self.assertIn(b'Saved book title: Harry Potter and the Order of the Phoenix', resp.data)
        with app.app_context():
            b = Book.query.filter_by(title='Harry Potter and the Order of the Phoenix').first()
            self.assertIsNotNone(b)
            self.assertEqual(b.author, 'J.K. Rowling')
            self.assertEqual(b.isbn, '0439358078')
            self.assertEqual(b.publish_year, 2003)
            self.assertEqual(b.page_count, 870)
            self.assertEqual(b.cover_edition_key, 'OL26486989M')
            self.assertAlmostEqual(b.rating, 4.5, places=2)

    def test_view_books_with_inserted(self):
        # Insert books directly into DB then list
        with app.app_context():
            db.session.add(Book(title='Little Beaver and the echo', author='Amy MacDonald', isbn='0399222030', publish_year=1990, page_count=32, rating=4.1))
            db.session.add(Book(title='Swan Song', author='Robert R. McCammon', isbn='1501131427', publish_year=2016, page_count=956, rating=4.4))
            db.session.add(Book(title='Harry Potter and the Order of the Phoenix', author='J.K. Rowling', isbn='0439358078', publish_year=2003, page_count=870, rating=4.5))
            db.session.commit()
        resp = self.client.get('/view_books')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Little Beaver and the echo', resp.data)
        self.assertIn(b'Swan Song', resp.data)
        self.assertIn(b'Harry Potter and the Order of the Phoenix', resp.data)

if __name__ == '__main__':
    unittest.main()
