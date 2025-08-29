"""
Release-4: Flask + sqlite3 API for CRUD on myTable (IP, DATE, URL).
Endpoints:
- GET /getdbdata: List all rows.
- POST /postdbdata: Add new row if IP not present.
- PUT /putdbdata: Update full row if IP present.
- PATCH /patchdbdata: Update DATE if IP present.
- DELETE /deletedbdata: Delete row if IP present.
All request/response contracts, field names, and messages are unchanged.
"""

import flask
import sqlite3

DB_NAME = "mydb.sqlite3"
TABLE_NAME = "myTable"
myapp = flask.Flask("MyAPIApp")

# --- DB Helpers ---
def get_connection():
    """Return a sqlite3 connection to DB_NAME."""
    return sqlite3.connect(DB_NAME)

def init_schema():
    """Create table if not exists (IP TEXT, DATE TEXT, URL TEXT)."""
    with get_connection() as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                IP TEXT,
                DATE TEXT,
                URL TEXT
            )
        """)
        conn.commit()

def fetch_all_rows():
    """Return all rows from myTable as list of dicts."""
    with get_connection() as conn:
        cur = conn.execute(f"SELECT * FROM {TABLE_NAME}")
        rows = [dict(zip(["IP", "DATE", "URL"], row)) for row in cur.fetchall()]
    return rows

def select_by_ip(ip):
    """Return row dict for given IP, or None."""
    with get_connection() as conn:
        cur = conn.execute(f"SELECT * FROM {TABLE_NAME} WHERE IP=?", (ip,))
        row = cur.fetchone()
        return dict(zip(["IP", "DATE", "URL"], row)) if row else None

def insert_row(ip, dt, url):
    """Insert new row."""
    with get_connection() as conn:
        conn.execute(f"INSERT INTO {TABLE_NAME} (IP, DATE, URL) VALUES (?, ?, ?)", (ip, dt, url))
        conn.commit()

def update_full(ip, dt, url):
    """Update DATE and URL for given IP."""
    with get_connection() as conn:
        conn.execute(f"UPDATE {TABLE_NAME} SET DATE=?, URL=? WHERE IP=?", (dt, url, ip))
        conn.commit()

def update_partial_date(ip, dt):
    """Update only DATE for given IP."""
    with get_connection() as conn:
        conn.execute(f"UPDATE {TABLE_NAME} SET DATE=? WHERE IP=?", (dt, ip))
        conn.commit()

def delete_by_ip(ip):
    """Delete row for given IP."""
    with get_connection() as conn:
        conn.execute(f"DELETE FROM {TABLE_NAME} WHERE IP=?", (ip,))
        conn.commit()

# --- Routes ---
@myapp.route("/getdbdata", methods=["GET"])
def getdbdata():
    """GET: Return all rows as JSON list."""
    rows = fetch_all_rows()
    print(rows)
    return flask.jsonify(rows)

@myapp.route("/postdbdata", methods=["POST"])
def postdbdata():
    """POST: Add new row if IP not present."""
    data = flask.request.get_json()
    ip = data["IP"]
    dt = data["DATE"]
    url = data["URL"]
    if select_by_ip(ip):
        return "Record already exists!"
    insert_row(ip, dt, url)
    return "New record added"

@myapp.route("/putdbdata", methods=["PUT"])
def putdbdata():
    """PUT: Update full row if IP present."""
    data = flask.request.get_json()
    ip = data["IP"]
    dt = data["DATE"]
    url = data["URL"]
    if not select_by_ip(ip):
        return "Record Not present to update!"
    update_full(ip, dt, url)
    return "Record Updated"

@myapp.route("/patchdbdata", methods=["PATCH"])
def patchdbdata():
    """PATCH: Update only DATE if IP present."""
    data = flask.request.get_json()
    ip = data["IP"]
    dt = data["DATE"]
    if not select_by_ip(ip):
        return "Record Not present to update!"
    update_partial_date(ip, dt)
    return "Record Updated"

@myapp.route("/deletedbdata", methods=["DELETE"])
def deletedbdata():
    """DELETE: Delete row if IP present."""
    data = flask.request.get_json()
    ip = data["IP"]
    if not select_by_ip(ip):
        return "Record Not present to Delete!"
    delete_by_ip(ip)
    return "Record Deleted"

if __name__ == "__main__":
    init_schema()
    myapp.run(host="127.0.0.1", port=5000)
