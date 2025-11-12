# Todo API Project - Copilot Instructions

This is a Python FastAPI project for managing todos with full CRUD operations.

## Project Structure
- `main.py` - FastAPI application with todo endpoints
- `requirements.txt` - Python dependencies (FastAPI, Uvicorn, Pydantic)
- `README.md` - Project documentation and setup instructions

## Development
- Python 3.11+ environment configured
- FastAPI server runs on http://localhost:8000
- Interactive API docs available at http://localhost:8000/docs
- VS Code task configured for running the server

## API Endpoints
- GET `/` - Welcome message
- GET `/todos` - Get all todos
- GET `/todos/{id}` - Get specific todo
- POST `/todos` - Create new todo
- PUT `/todos/{id}` - Update todo
- DELETE `/todos/{id}` - Delete todo
- GET `/health` - Health check