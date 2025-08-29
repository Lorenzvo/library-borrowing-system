from flask import Flask, request, redirect, url_for, render_template_string
import requests

app = Flask(__name__)
USERS_API = "http://localhost:5001"
BOOKS_API = "http://localhost:5002"

FOOTER = '<hr><p><small>No JS/CSS. Server-rendered HTML only. Data via Users(5001) & Books(5002).</small></p>'

NAV = (
    '<nav>'
    '<a href="/">Home</a> | '
    '<a href="/users">Users</a> | '
    '<a href="/books">Books</a> | '
    '<a href="/borrow">Borrow</a> | '
    '<a href="/return">Return</a> | '
    '<a href="/loans">Loans</a> | '
    '<a href="/about">About</a>'
    '</nav><hr>'
)

@app.route("/")
def home():
    html = f'''
    <h1>Library Borrowing System — Portal</h1>
    <p>Consolidates Users & Books microservices.</p>
    {NAV}
    <table border="1" cellpadding="6">
      <tr><th>Service</th><th>Base URL</th><th>Main Endpoints</th></tr>
      <tr><td>Users</td><td>{USERS_API}</td><td>/api/users, /api/health</td></tr>
      <tr><td>Books</td><td>{BOOKS_API}</td><td>/api/books, /api/borrow, /api/return, /api/loans, /api/overdue</td></tr>
    </table>
    {FOOTER}
    '''
    return render_template_string(html)

@app.route("/about")
def about():
    html = f'''
    <h1>About the Portal</h1>
    {NAV}
    <p>This Portal has no database. It integrates Users and Books microservices via API-only calls.</p>
    <p>Each backend uses its own SQLite DB. The Portal only renders HTML from API data.</p>
    {FOOTER}
    '''
    return render_template_string(html)

@app.route("/users", methods=["GET", "POST"])
def users():
    error = request.args.get("error")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        try:
            resp = requests.post(f"{USERS_API}/api/users", json={"name": name, "email": email}, timeout=3)
            if resp.status_code == 201:
                return redirect(url_for("users"))
            else:
                err = resp.json().get("error", "Unknown error")
                return redirect(url_for("users", error=err))
        except Exception:
            return redirect(url_for("users", error="Error contacting Users Service"))
    try:
        resp = requests.get(f"{USERS_API}/api/users", timeout=3)
        users_list = resp.json() if resp.status_code == 200 else []
    except Exception:
        users_list = []
        error = error or "Error contacting Users Service"
    table = '<table border="1" cellpadding="6"><tr><th>ID</th><th>Name</th><th>Email</th></tr>'
    for u in users_list:
        table += f'<tr><td>{u["id"]}</td><td>{u["name"]}</td><td>{u["email"]}</td></tr>'
    table += '</table>'
    form = '''<fieldset><legend>Create User</legend>
    <form method="post" action="/users">
      Name: <input name="name" required> Email: <input name="email" required>
      <button type="submit">Create</button>
    </form></fieldset>'''
    html = f'''<h1>Users</h1>{NAV}
    {table}
    {'<p><strong>Error:</strong> ' + error + '</p>' if error else ''}
    {form}
    {FOOTER}'''
    return render_template_string(html)

@app.route("/books", methods=["GET", "POST"])
def books():
    error = request.args.get("error")
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "Unknown").strip() or "Unknown"
        try:
            resp = requests.post(f"{BOOKS_API}/api/books", json={"title": title, "author": author}, timeout=3)
            if resp.status_code == 201:
                return redirect(url_for("books"))
            else:
                err = resp.json().get("error", "Unknown error")
                return redirect(url_for("books", error=err))
        except Exception:
            return redirect(url_for("books", error="Error contacting Books Service"))
    try:
        resp = requests.get(f"{BOOKS_API}/api/books", timeout=3)
        books_list = resp.json() if resp.status_code == 200 else []
    except Exception:
        books_list = []
        error = error or "Error contacting Books Service"
    table = '<table border="1" cellpadding="6"><tr><th>ID</th><th>Title</th><th>Author</th><th>Status</th></tr>'
    for b in books_list:
        table += f'<tr><td>{b["id"]}</td><td>{b["title"]}</td><td>{b["author"]}</td><td>{b["status"]}</td></tr>'
    table += '</table>'
    # Available Books table (if endpoint exists)
    try:
        resp_avail = requests.get(f"{BOOKS_API}/api/books/available", timeout=3)
        avail_books = resp_avail.json() if resp_avail.status_code == 200 else []
        if avail_books:
            avail_table = '<h2>Available Books</h2><table border="1" cellpadding="6"><tr><th>ID</th><th>Title</th><th>Author</th></tr>'
            for b in avail_books:
                avail_table += f'<tr><td>{b["id"]}</td><td>{b["title"]}</td><td>{b["author"]}</td></tr>'
            avail_table += '</table>'
        else:
            avail_table = ''
    except Exception:
        avail_table = ''
    form = '''<fieldset><legend>Add Book</legend>
    <form method="post" action="/books">
      Title: <input name="title" required> Author: <input name="author">
      <button type="submit">Add</button>
    </form></fieldset>'''
    html = f'''<h1>Books</h1>{NAV}
    {table}
    {'<p><strong>Error:</strong> ' + error + '</p>' if error else ''}
    {form}
    {avail_table if avail_table else ''}
    {FOOTER}'''
    return render_template_string(html)

@app.route("/borrow", methods=["GET", "POST"])
def borrow():
    error = request.args.get("error")
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        book_id = request.form.get("book_id", "").strip()
        days = request.form.get("days", "").strip()
        payload = {"user_id": user_id, "book_id": book_id}
        if days.isdigit():
            payload["days"] = int(days)
        try:
            resp = requests.post(f"{BOOKS_API}/api/borrow", json=payload, timeout=3)
            if resp.status_code == 201:
                return redirect(url_for("loans", user_id=user_id))
            else:
                err = resp.json().get("error", "Unknown error")
                return redirect(url_for("borrow", error=err))
        except Exception:
            return redirect(url_for("borrow", error="Error contacting Books Service"))
    form = '''<fieldset><legend>Borrow Book</legend>
    <form method="post" action="/borrow">
      User ID: <input name="user_id" required> Book ID: <input name="book_id" required> Days: <input name="days" type="number" min="1">
      <button type="submit">Borrow</button>
    </form></fieldset>'''
    html = f'''<h1>Borrow</h1>{NAV}
    {'<p><strong>Error:</strong> ' + error + '</p>' if error else ''}
    {form}
    {FOOTER}'''
    return render_template_string(html)

@app.route("/return", methods=["GET", "POST"])
def return_book():
    error = request.args.get("error")
    if request.method == "POST":
        book_id = request.form.get("book_id", "").strip()
        try:
            resp = requests.post(f"{BOOKS_API}/api/return", json={"book_id": book_id}, timeout=3)
            if resp.status_code == 200:
                return redirect(url_for("loans"))
            else:
                err = resp.json().get("error", "Unknown error")
                return redirect(url_for("return_book", error=err))
        except Exception:
            return redirect(url_for("return_book", error="Error contacting Books Service"))
    form = '''<fieldset><legend>Return Book</legend>
    <form method="post" action="/return">
      Book ID: <input name="book_id" required>
      <button type="submit">Return</button>
    </form></fieldset>'''
    html = f'''<h1>Return</h1>{NAV}
    {'<p><strong>Error:</strong> ' + error + '</p>' if error else ''}
    {form}
    {FOOTER}'''
    return render_template_string(html)

@app.route("/loans")
def loans():
    user_id = request.args.get("user_id")
    open_filter = request.args.get("open")
    error = request.args.get("error")
    overdue_table = ''
    # Overdue loans table (if endpoint exists)
    try:
        resp_overdue = requests.get(f"{BOOKS_API}/api/overdue", timeout=3)
        overdue_loans = resp_overdue.json() if resp_overdue.status_code == 200 else []
        if overdue_loans:
            overdue_table = '<h2>Overdue Loans</h2><table border="1" cellpadding="6"><tr><th>Loan ID</th><th>User ID</th><th>Book ID</th><th>Borrowed</th><th>Due Date</th></tr>'
            for l in overdue_loans:
                overdue_table += f'<tr><td>{l["id"]}</td><td>{l["user_id"]}</td><td>{l["book_id"]}</td><td>{l["borrowed_at"]}</td><td>{l["due_date"]}</td></tr>'
            overdue_table += '</table>'
    except Exception:
        overdue_table = ''
    # Normal loans table
    params = {}
    if user_id:
        params["user_id"] = user_id
    if open_filter in ("true", "false"):
        params["open"] = open_filter
    try:
        resp = requests.get(f"{BOOKS_API}/api/loans", params=params, timeout=3)
        loans_list = resp.json() if resp.status_code == 200 else []
    except Exception:
        loans_list = []
        error = error or "Error contacting Books Service"
    table = '<table border="1" cellpadding="6"><tr><th>Loan ID</th><th>User ID</th><th>Book ID</th><th>Borrowed</th><th>Returned</th></tr>'
    for l in loans_list:
        table += f'<tr><td>{l["id"]}</td><td>{l["user_id"]}</td><td>{l["book_id"]}</td><td>{l["borrowed_at"]}</td><td>{l["returned_at"]}</td></tr>'
    table += '</table>'
    html = f'''<h1>Loans</h1>{NAV}
    {overdue_table if overdue_table else ''}
    {table}
    {'<p><strong>Error:</strong> ' + error + '</p>' if error else ''}
    {FOOTER}'''
    return render_template_string(html)

if __name__ == "__main__":
    app.run(port=5000)
