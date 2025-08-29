"""
Books Service: Flask app for book and loan management with SQLite (books.db).
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    """Book model."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(80), nullable=False, default="Unknown")
    status = db.Column(db.String(16), nullable=False, default="AVAILABLE")

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "author": self.author, "status": self.status}

class Loan(db.Model):
    """Loan model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    borrowed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    returned_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "user_id": self.user_id, "book_id": self.book_id, "borrowed_at": self.borrowed_at, "returned_at": self.returned_at}

@app.route("/")
def home():
    """Pleasant semantic HTML home page."""
    html = '''
    <h1>Books Service</h1>
    <p>Microservice for managing books and loans.</p>
    <nav>
      <a href="/">Home</a> |
      <a href="/about">About</a> |
      <a href="/api/books">API: Books</a>
    </nav>
    <table border="1" cellpadding="6">
      <tr><th>Method</th><th>Path</th><th>Description</th></tr>
      <tr><td>POST</td><td>/api/books</td><td>Create a new book</td></tr>
      <tr><td>GET</td><td>/api/books</td><td>List all books</td></tr>
      <tr><td>POST</td><td>/api/borrow</td><td>Borrow a book</td></tr>
      <tr><td>POST</td><td>/api/return</td><td>Return a book</td></tr>
      <tr><td>GET</td><td>/api/loans</td><td>List all loans</td></tr>
    </table>
    <details><summary>Sample: User validation</summary><pre><code>GET http://localhost:5001/api/users/&lt;id&gt;
    </code></pre></details>
    '''
    return html, 200

@app.route("/about")
def about():
    """Simple HTML about page."""
    html = '''
    <h1>About Books Service</h1>
    <p>This service manages books and loans in its own SQLite database.</p>
    <table border="1" cellpadding="6">
      <tr><th>Database File</th><th>Table</th><th>Columns</th></tr>
      <tr><td>books.db</td><td>Book</td><td>id (PK), title (TEXT), author (TEXT), status (TEXT)</td></tr>
      <tr><td>books.db</td><td>Loan</td><td>id (PK), user_id (INT), book_id (INT), borrowed_at (DATETIME), returned_at (DATETIME)</td></tr>
    </table>
    <ul>
      <li>Books are AVAILABLE or BORROWED</li>
      <li>Only AVAILABLE books can be borrowed</li>
      <li>Returning sets status to AVAILABLE</li>
    </ul>
    '''
    return html, 200

@app.route("/api/books", methods=["POST"])
def create_book():
    """Create a new book."""
    data = request.get_json()
    title = data.get("title")
    author = data.get("author", "Unknown")
    if not title:
        return jsonify({"error": "Missing title."}), 400
    book = Book(title=title, author=author, status="AVAILABLE")
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201

@app.route("/api/books", methods=["GET"])
def get_books():
    """Get all books."""
    books = Book.query.all()
    return jsonify([b.to_dict() for b in books]), 200

@app.route("/api/borrow", methods=["POST"])
def borrow_book():
    """Borrow a book."""
    data = request.get_json()
    user_id = data.get("user_id")
    book_id = data.get("book_id")
    if not user_id or not book_id:
        return jsonify({"error": "Missing user_id or book_id."}), 400
    # Validate user via Users Service
    user_resp = requests.get(f"http://localhost:5001/api/users/{user_id}")
    if user_resp.status_code == 404:
        return jsonify({"error": "User not found."}), 404
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found."}), 404
    if book.status != "AVAILABLE":
        return jsonify({"error": "Book not available."}), 409
    open_loan = Loan.query.filter_by(book_id=book_id, returned_at=None).first()
    if open_loan:
        return jsonify({"error": "Book already on loan."}), 409
    loan = Loan(user_id=user_id, book_id=book_id)
    book.status = "BORROWED"
    db.session.add(loan)
    db.session.commit()
    return jsonify({"message": "Borrowed", "loan_id": loan.id}), 201

@app.route("/api/return", methods=["POST"])
def return_book():
    """Return a book."""
    data = request.get_json()
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Missing book_id."}), 400
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found."}), 404
    if book.status != "BORROWED":
        return jsonify({"error": "Book not borrowed."}), 409
    open_loan = Loan.query.filter_by(book_id=book_id, returned_at=None).first()
    if not open_loan:
        return jsonify({"error": "No open loan for this book."}), 409
    open_loan.returned_at = datetime.utcnow()
    book.status = "AVAILABLE"
    db.session.commit()
    return jsonify({"message": "Returned", "loan_id": open_loan.id}), 200

@app.route("/api/loans", methods=["GET"])
def get_loans():
    """Get all loans."""
    loans = Loan.query.all()
    return jsonify([l.to_dict() for l in loans]), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002)
