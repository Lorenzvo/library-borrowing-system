@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200
"""
Users Service: Flask app for user management with SQLite (users.db).
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Health endpoint
@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

class User(db.Model):
    """User model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email}



@app.route("/")
def home():
        """Pleasant semantic HTML home page."""
        nav = (
            '<nav>'
            '<a href="http://localhost:5000/">Portal Home</a> | '
            '<a href="http://localhost:5000/users">Portal Users</a> | '
            '<a href="http://localhost:5000/books">Portal Books</a>'
            '</nav><hr>'
        )
        html = f'''
        <h1>Users Service</h1>
        {nav}
        <p>A minimal microservice for user management.</p>
        <table border="1" cellpadding="6">
            <tr><th>Method</th><th>Path</th><th>Description</th></tr>
            <tr><td>POST</td><td>/api/users</td><td>Create a new user</td></tr>
            <tr><td>GET</td><td>/api/users</td><td>List all users</td></tr>
            <tr><td>GET</td><td>/api/users/&lt;id&gt;</td><td>Get user by ID</td></tr>
        </table>
        <details><summary>Sample cURL</summary><pre><code>curl -X POST http://localhost:5001/api/users -H "Content-Type: application/json" -d '{"name": "Alice", "email": "alice@example.com"}'
        </code></pre></details>
        '''
        return html, 200


@app.route("/about")
def about():
        """Simple HTML about page."""
        nav = (
            '<nav>'
            '<a href="http://localhost:5000/">Portal Home</a> | '
            '<a href="http://localhost:5000/users">Portal Users</a> | '
            '<a href="http://localhost:5000/books">Portal Books</a>'
            '</nav><hr>'
        )
        html = f'''
        <h1>About Users Service</h1>
        {nav}
        <p>This service manages users in its own SQLite database.</p>
        <table border="1" cellpadding="6">
            <tr><th>Database File</th><th>Table</th><th>Columns</th></tr>
            <tr><td>users.db</td><td>User</td><td>id (PK), name (TEXT), email (TEXT, UNIQUE)</td></tr>
        </table>
        '''
        return html, 200


@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user with validation."""
    data = request.get_json()
    name = (data or {}).get("name", "").strip()
    email = (data or {}).get("email", "").strip()
    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists."}), 409
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201
@app.route("/docs")
def docs():
        """Users API documentation page."""
        html = '''
        <h1>Users API Docs</h1>
        <nav><a href="/">Home</a> | <a href="/about">About</a> | <a href="/docs">Docs</a> | <a href="/api/health">Health</a></nav>
        <hr>
        <h2>Endpoints</h2>
        <table border="1" cellpadding="6">
            <tr><th>Method</th><th>Path</th><th>Notes</th></tr>
            <tr><td>POST</td><td>/api/users</td><td>Create user (name, email)</td></tr>
            <tr><td>GET</td><td>/api/users</td><td>List all users</td></tr>
            <tr><td>GET</td><td>/api/users/&lt;id&gt;</td><td>Get user by ID</td></tr>
            <tr><td>GET</td><td>/api/health</td><td>Health check</td></tr>
        </table>
        <hr>
        <h2>Examples</h2>
        <details><summary>POST /api/users</summary><pre><code>curl -X POST http://localhost:5001/api/users -H "Content-Type: application/json" -d '{"name": "Alice", "email": "alice@example.com"}'
        </code></pre></details>
        <details><summary>GET /api/users</summary><pre><code>curl http://localhost:5001/api/users
        </code></pre></details>
        <details><summary>GET /api/users/&lt;id&gt;</summary><pre><code>curl http://localhost:5001/api/users/1
        </code></pre></details>
        <details><summary>Health check</summary><pre><code>curl http://localhost:5001/api/health
        </code></pre></details>
        <hr>
        <h2>Error Cases</h2>
        <table border="1" cellpadding="6">
            <tr><th>Status</th><th>When</th><th>Payload</th></tr>
            <tr><td>400</td><td>Missing/empty name or email</td><td>{"error": "Name and email are required."}</td></tr>
            <tr><td>409</td><td>Duplicate email</td><td>{"error": "Email already exists."}</td></tr>
            <tr><td>404</td><td>User not found</td><td>{"error": "User not found."}</td></tr>
        </table>
        '''
        return html, 200

@app.route("/api/users", methods=["GET"])
def get_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Get user by ID."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user.to_dict()), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5001)
