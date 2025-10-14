import unittest
import json
from flask_testing import TestCase
from app import app, db, Book

class BookRecommendationTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_unit_positive_recommendation(self):
        book1 = Book(isbn='9780140328721', title='Foundation', author='Isaac Asimov', publish_year=2004, page_count=350)
        book2 = Book(isbn='9780547928227', title='The Hobbit', author='J.R.R. Tolkien', publish_year=2012, page_count=300)
        db.session.add(book1)
        db.session.add(book2)
        db.session.commit()
        response = self.client.get('/get_recommendation')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Recommendations', response.data)
        self.assertIn(b'Foundation', response.data)

    def test_insufficient_books(self):
        book1 = Book(isbn='9780140328721', title='Foundation', author='Isaac Asimov', publish_year=2004, page_count=350)
        db.session.add(book1)
        db.session.commit()
        response = self.client.get('/get_recommendation')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not enough books collected', response.data)
        self.assertIn(b'We have 1 books', response.data)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Recommendation System', response.data)

    def test_collect_book_data(self):
        response = self.client.post('/collect', data={'user_input': 'Foundation'})
        self.assertTrue(response.status_code in [200, 500])

    def test_view_books_empty(self):
        response = self.client.get('/view_books')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No books collected yet', response.data)

    def test_view_books_with_data(self):
        book1 = Book(isbn='9780140328721', title='Foundation', author='Isaac Asimov', publish_year=2004, page_count=350)
        db.session.add(book1)
        db.session.commit()
        response = self.client.get('/view_books')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Collected Books (1 total)', response.data)
        self.assertIn(b'Foundation', response.data)

if __name__ == '__main__':
    unittest.main()
