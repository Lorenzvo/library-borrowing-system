from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

rate_limit = {}

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
    due_date = db.Column(db.DateTime, nullable=True)
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "borrowed_at": self.borrowed_at,
            "returned_at": self.returned_at,
            "due_date": self.due_date
        }


@app.route("/")
def home():
    nav = (
        '<nav>'
        '<a href="http://localhost:5000/">Portal Home</a> | '
        '<a href="http://localhost:5000/borrow">Portal Borrow</a> | '
        '<a href="http://localhost:5000/return">Portal Return</a> | '
        '<a href="http://localhost:5000/loans">Portal Loans</a>'
        '</nav><hr>'
    )
    html = f'''
    <h1>Books Service</h1>
    {nav}
    <p>This service manages books and loans for the library system.</p>
    <table border="1" cellpadding="6">
        <tr><th>Endpoint</th><th>Method</th><th>Notes</th></tr>
        <tr><td>/api/books</td><td>GET, POST</td><td>List or add books</td></tr>
        <tr><td>/api/borrow</td><td>POST</td><td>Borrow a book</td></tr>
        <tr><td>/api/return</td><td>POST</td><td>Return a book</td></tr>
        <tr><td>/api/loans</td><td>GET</td><td>List loans</td></tr>
        <tr><td>/api/overdue</td><td>GET</td><td>List overdue loans</td></tr>
        <tr><td>/docs</td><td>GET</td><td>API documentation</td></tr>
    </table>
    '''
    return html, 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002)


@app.route("/about")
def about():
    nav = (
        '<nav>'
        '<a href="http://localhost:5000/">Portal Home</a> | '
        '<a href="http://localhost:5000/borrow">Portal Borrow</a> | '
        '<a href="http://localhost:5000/return">Portal Return</a> | '
        '<a href="http://localhost:5000/loans">Portal Loans</a>'
        '</nav><hr>'
    )
    html = f'''
    <h1>About Books Service</h1>
    {nav}
    <p>Independent microservice with its own SQLite database.</p>
    <p>Handles book management and loans via API.</p>
    '''
    return html, 200

@app.route("/api/books", methods=["POST"])
def create_book():
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
    books = Book.query.all()
    return jsonify([b.to_dict() for b in books]), 200

@app.route("/api/books/available", methods=["GET"])
def get_available_books():
    books = Book.query.filter_by(status="AVAILABLE").all()
    return jsonify([b.to_dict() for b in books]), 200

@app.route("/api/borrow", methods=["POST"])
def borrow_book():
    ip = request.remote_addr
    now = time.time()
    attempts = rate_limit.get(ip, [])
    attempts = [t for t in attempts if now - t < 60]
    if len(attempts) >= 5:
        return jsonify({"error": "rate limit exceeded"}), 429
    attempts.append(now)
    rate_limit[ip] = attempts

    data = request.get_json()
    user_id = data.get("user_id")
    book_id = data.get("book_id")
    days = data.get("days")
    if not user_id or not book_id:
        return jsonify({"error": "Missing user_id or book_id."}), 400
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
    due_date = None
    if isinstance(days, int) and days > 0:
        due_date = datetime.utcnow() + timedelta(days=days)
    loan = Loan(user_id=user_id, book_id=book_id, due_date=due_date)
    book.status = "BORROWED"
    db.session.add(loan)
    db.session.commit()
    return jsonify({"message": "Borrowed", "loan_id": loan.id}), 201

@app.route("/api/return", methods=["POST"])
def return_book():
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
    user_id = request.args.get("user_id", type=int)
    open_filter = request.args.get("open")
    query = Loan.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if open_filter is not None:
        if open_filter.lower() == "true":
            query = query.filter_by(returned_at=None)
        elif open_filter.lower() == "false":
            query = query.filter(Loan.returned_at.isnot(None))
    loans = query.all()
    return jsonify([l.to_dict() for l in loans]), 200

@app.route("/api/overdue", methods=["GET"])
def get_overdue():
    now = datetime.utcnow()
    overdue_loans = Loan.query.filter(
        Loan.returned_at.is_(None),
        Loan.due_date.isnot(None),
        Loan.due_date < now
    ).all()
    return jsonify([l.to_dict() for l in overdue_loans]), 200

@app.route("/docs")
def docs():
        html = '''
        <h1>Books API Docs</h1>
        <nav><a href="/">Home</a> | <a href="/about">About</a> | <a href="/docs">Docs</a></nav>
        <hr>
        <h2>Endpoints</h2>
        <table border="1" cellpadding="6">
            <tr><th>Method</th><th>Path</th><th>Notes</th></tr>
            <tr><td>POST</td><td>/api/books</td><td>Create book (title, author)</td></tr>
            <tr><td>GET</td><td>/api/books</td><td>List all books</td></tr>
            <tr><td>GET</td><td>/api/books/available</td><td>List available books</td></tr>
            <tr><td>POST</td><td>/api/borrow</td><td>Borrow a book (optional "days" param sets due_date)</td></tr>
            <tr><td>POST</td><td>/api/return</td><td>Return a book</td></tr>
            <tr><td>GET</td><td>/api/loans</td><td>List loans (filters: user_id, open)</td></tr>
            <tr><td>GET</td><td>/api/overdue</td><td>List overdue loans</td></tr>
        </table>
        <hr>
        <h2>Examples</h2>
        <details><summary>POST /api/borrow</summary><pre><code>curl -X POST http://localhost:5002/api/borrow -H "Content-Type: application/json" -d '{"user_id": 1, "book_id": 1, "days": 3}'
        </code></pre></details>
        <details><summary>Borrow with due date</summary><pre><code>curl -X POST http://localhost:5002/api/borrow -H "Content-Type: application/json" -d '{"user_id": 1, "book_id": 1, "days": 3}'
        </code></pre></details>
        <details><summary>Overdue loans</summary><pre><code>curl http://localhost:5002/api/overdue
        </code></pre></details>
        <details><summary>Rate limit example</summary><pre><code>429 {"error": "rate limit exceeded"}
        </code></pre></details>
        <hr>
        <h2>Rules & Notes</h2>
        <table border="1" cellpadding="6">
            <tr><th>Rule</th></tr>
            <tr><td>Must validate user via Users API before borrowing</td></tr>
            <tr><td>Conflicts return 409</td></tr>
            <tr><td>Borrow accepts optional "days" param for due_date</td></tr>
            <tr><td>More than 5 borrow attempts per minute per IP returns 429</td></tr>
            <tr><td>/api/overdue returns open loans past due_date</td></tr>
        </table>
        '''
        return html, 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002)