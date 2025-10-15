# BookTaste

A small Flask-based book recommendation/collection app that fetches book details from the Open Library API and stores collected books in a local SQLite database. It offers a simple UI to collect books and a basic recommendation endpoint based on page count, publish year and rating.

## Features

- Collect book metadata (title, author, publish year, page count, ISBN) from Open Library.
- Store collected books in `books.db` (SQLite) using SQLAlchemy.
- Basic recommendation logic that scores books by length, recency and rating.
- Simple HTML forms for collecting and viewing books, and an endpoint to get recommendations.

## Quick start (macOS / zsh)

1. Clone the repo and change into the project folder:

```
git clone <repo-url>
cd Bookrec/Bookrec
```

2. Create a virtual environment and activate it (recommended):

```
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies. If you don't have a `requirements.txt`, install the minimal packages used by the app:

```
pip install Flask flask_sqlalchemy
# Optional (used by tests):
pip install flask-testing
```

Tip: to create a `requirements.txt` for the current environment:

```
pip freeze > requirements.txt
```

4. Run the app:

```
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Running tests

This repo includes a `test.py` file which uses `unittest` and `flask-testing`.
To run tests:


pip install flask-testing
python -m unittest test.py


Note: tests create an in-memory SQLite DB and won't modify `books.db`.

## Important notes about ISBN handling

- The `Book` model uses `isbn` as the primary key and it must be non-null. The app queries Open Library and expects an ISBN for each collected book. However, some Open Library results may not include an ISBN.
- To avoid database errors when Open Library doesn't return an ISBN, the app currently generates a synthetic ID in the form `gen-<uuid>` and stores it as the book's `isbn`. This keeps a unique primary key while allowing collection of items that don't have a genuine ISBN.

Considerations / alternatives:
- If you prefer to require real ISBNs, change the UI to require the ISBN when collecting books and skip saving results without an ISBN.
- A better long-term model is to add a dedicated integer `id` primary key (autoincrement) and make `isbn` an optional, indexed column. That requires a migration (Alembic) if you already have data.



## License

This project is provided as-is for learning and demonstration purposes.
