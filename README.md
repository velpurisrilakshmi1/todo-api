# Todo API

A simple REST API built with FastAPI for managing todos. Perfect for beginners following the backend development roadmap.

## Features

- ✅ Create, read, update, and delete todos (CRUD operations)
- ✅ RESTful API endpoints
- ✅ Data validation with Pydantic
- ✅ Interactive API documentation with Swagger UI
- ✅ JSON responses
- ✅ Error handling

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/todos` | Get all todos |
| GET | `/todos/{id}` | Get a specific todo by ID |
| POST | `/todos` | Create a new todo |
| PUT | `/todos/{id}` | Update an existing todo |
| DELETE | `/todos/{id}` | Delete a todo |
| GET | `/health` | Health check |

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone or download this project**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the API

1. **Start the development server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Open your browser** and go to:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Usage Examples

### Create a new todo
```bash
curl -X POST "http://localhost:8000/todos" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Learn FastAPI",
       "description": "Complete the FastAPI tutorial",
       "completed": false
     }'
```

### Get all todos
```bash
curl -X GET "http://localhost:8000/todos"
```

### Update a todo
```bash
curl -X PUT "http://localhost:8000/todos/{todo_id}" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Learn FastAPI",
       "description": "Complete the FastAPI tutorial",
       "completed": true
     }'
```

## Project Structure

```
todo_api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
└── .github/
    └── copilot-instructions.md
```

## Git Setup & Version Control

### Prerequisites for Git
1. **Install Git**: Download from https://git-scm.com/download/win
2. **Configure Git** (run these commands after installation):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

### Initialize Repository & Commit
```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit your work
git commit -m "Initial FastAPI Todo API with SQLite database

- Complete CRUD operations for todos
- SQLite database integration with persistence
- Pydantic models for data validation
- Comprehensive documentation and comments
- Database viewer utility (view_todos.py)
- Workflow diagrams for learning"

# Connect to GitHub (replace with your repository URL)
git remote add origin https://github.com/yourusername/todo-api.git

# Push to GitHub
git push -u origin main
```

## Next Steps

This implementation now includes **SQLite database persistence**. For further enhancement, consider:

1. **User authentication** and authorization
2. **Advanced database features** (relationships, indexes)
3. **Input validation** and sanitization  
4. **API testing** (unit tests, integration tests)
5. **Logging** and monitoring
6. **Deployment** (Docker, cloud platforms)
7. **PostgreSQL migration** for production use

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: Lightning-fast ASGI server

## License

This project is for educational purposes.