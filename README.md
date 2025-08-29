# Library API

A minimal two-service Flask project for managing users and books in a library. Each service has its own SQLite database and communicates only via HTTP.

## Services & Ports
- **Users Service**: `users_service.py` (port 5001, SQLite: `users.db`)
- **Books Service**: `books_service.py` (port 5002, SQLite: `books.db`)

## Setup
```sh
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## How to Run Each Service
```sh
# Run Users Service
python users_service.py

# Run Books Service
python books_service.py
```

## cURL Samples

### Create a User
```sh
curl -X POST http://localhost:5001/users -H "Content-Type: application/json" -d '{"name": "Alice"}'
```

### Create a Book
```sh
curl -X POST http://localhost:5002/books -H "Content-Type: application/json" -d '{"title": "1984"}'
```

### Borrow a Book
```sh
curl -X POST http://localhost:5002/borrow -H "Content-Type: application/json" -d '{"user_id": 1, "book_id": 1}'
```

### Return a Book
```sh
curl -X POST http://localhost:5002/return -H "Content-Type: application/json" -d '{"user_id": 1, "book_id": 1}'
```

### List Loans
```sh
curl http://localhost:5002/loans
```

## Roadmap: Three Releases
1. **MVP**: Basic user/book CRUD, borrow/return, HTTP validation, error handling.
2. **Improvements**: Add search, pagination, better error messages, input validation.
3. **Production Ready**: Dockerization, authentication, deployment scripts, CI/CD.
