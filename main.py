# Import necessary libraries for our FastAPI application
from fastapi import FastAPI, HTTPException  # FastAPI framework and HTTP exception handling
from pydantic import BaseModel              # For data validation and serialization
from typing import List, Optional           # Type hints for better code readability
import uuid                                 # Generate unique IDs for todos
import aiosqlite                           # Async SQLite database operations
import os                                  # Operating system interface (not used but good to have)
from contextlib import asynccontextmanager  # For managing application startup/shutdown

# Database configuration
DATABASE_PATH = "todos.db"  # SQLite database file name (will be created automatically)

# DATA MODELS (Pydantic models for request/response validation)
# These define the structure of our data and automatically validate incoming requests

class TodoBase(BaseModel):
    """Base model that defines common todo fields"""
    title: str                           # Required: The todo title (must be a string)
    description: Optional[str] = None    # Optional: Todo description (can be None/null)
    completed: bool = False              # Default: New todos start as not completed

class TodoCreate(TodoBase):
    """Model for creating new todos (inherits all fields from TodoBase)"""
    pass  # No additional fields needed - just uses title, description, completed

class Todo(TodoBase):
    """Complete todo model with ID (used for responses from the API)"""
    id: str  # Unique identifier - added when todo is saved to database

# DATABASE FUNCTIONS
# These functions handle all interactions with the SQLite database

async def init_database():
    """Initialize the database and create tables if they don't exist"""
    # Connect to SQLite database (creates file if it doesn't exist)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create the todos table with the following structure:
        # - id: Unique identifier (PRIMARY KEY)
        # - title: Todo title (required, NOT NULL)
        # - description: Optional description
        # - completed: Boolean flag (defaults to FALSE)
        # - created_at: Timestamp when todo was created
        await db.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Save changes to the database
        await db.commit()

async def get_todos_from_db() -> List[Todo]:
    """Get all todos from database - returns a list of Todo objects"""
    # Connect to database
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Set row_factory to access columns by name (like a dictionary)
        db.row_factory = aiosqlite.Row
        
        # Execute SQL query to get all todos, ordered by newest first
        cursor = await db.execute('SELECT id, title, description, completed FROM todos ORDER BY created_at DESC')
        
        # Fetch all results from the query
        rows = await cursor.fetchall()
        
        # Convert database rows to Todo objects
        # **dict(row) unpacks the row dictionary as keyword arguments to Todo()
        return [Todo(**dict(row)) for row in rows]

async def get_todo_from_db(todo_id: str) -> Optional[Todo]:
    """Get a specific todo by ID from database - returns Todo object or None if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Set row_factory to access columns by name
        db.row_factory = aiosqlite.Row
        
        # Execute SQL query with parameter substitution (? prevents SQL injection)
        # The (todo_id,) tuple provides the value for the ? placeholder
        cursor = await db.execute('SELECT id, title, description, completed FROM todos WHERE id = ?', (todo_id,))
        
        # Fetch only one result (since ID should be unique)
        row = await cursor.fetchone()
        
        # Return Todo object if found, otherwise return None
        return Todo(**dict(row)) if row else None

async def create_todo_in_db(todo: TodoCreate) -> Todo:
    """Create a new todo in database - returns the created Todo object"""
    # Create a new Todo object with a unique ID
    new_todo = Todo(
        id=str(uuid.uuid4()),              # Generate unique ID (UUID = Universal Unique Identifier)
        title=todo.title,                  # Copy title from input
        description=todo.description,      # Copy description from input
        completed=todo.completed           # Copy completed status from input
    )
    
    # Connect to database and insert the new todo
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # INSERT SQL statement with parameter substitution for security
        await db.execute(
            'INSERT INTO todos (id, title, description, completed) VALUES (?, ?, ?, ?)',
            (new_todo.id, new_todo.title, new_todo.description, new_todo.completed)
        )
        # Save changes to database
        await db.commit()
    
    # Return the created todo object
    return new_todo

async def update_todo_in_db(todo_id: str, todo_update: TodoCreate) -> Optional[Todo]:
    """Update a todo in database - returns updated Todo object or None if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Execute UPDATE SQL statement
        cursor = await db.execute(
            'UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?',
            (todo_update.title, todo_update.description, todo_update.completed, todo_id)
        )
        # Save changes to database
        await db.commit()
        
        # Check if any row was actually updated
        # cursor.rowcount tells us how many rows were affected by the query
        if cursor.rowcount == 0:
            return None  # No todo found with that ID
        
        # Return the updated todo object
        return Todo(
            id=todo_id,                            # Keep the same ID
            title=todo_update.title,               # New title
            description=todo_update.description,   # New description
            completed=todo_update.completed        # New completed status
        )

async def delete_todo_from_db(todo_id: str) -> bool:
    """Delete a todo from database - returns True if deleted, False if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Execute DELETE SQL statement
        cursor = await db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        # Save changes to database
        await db.commit()
        
        # Return True if a row was deleted, False if no todo was found with that ID
        return cursor.rowcount > 0

# APPLICATION STARTUP/SHUTDOWN MANAGEMENT
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle - runs code when app starts and stops"""
    # STARTUP: This code runs when the application starts
    await init_database()  # Create database tables if they don't exist
    print(f"📄 Database initialized: {DATABASE_PATH}")
    
    yield  # This is where the application runs (yields control to FastAPI)
    
    # SHUTDOWN: Code after yield runs when application stops
    # (cleanup code would go here if needed)

# CREATE FASTAPI APPLICATION INSTANCE
app = FastAPI(
    title="Todo API",                                           # API title (shown in docs)
    description="A simple Todo API built with FastAPI and SQLite",  # API description
    version="2.0.0",                                           # API version
    lifespan=lifespan                                          # Attach startup/shutdown handler
)

# API ENDPOINTS (Routes)
# These are the URLs that clients can call to interact with our API

# ROOT ENDPOINT - GET /
@app.get("/")
async def root():
    """Welcome message - simple endpoint to test if API is working"""
    return {"message": "Welcome to Todo API with SQLite Database! 🗄️"}

# GET ALL TODOS - GET /todos
@app.get("/todos", response_model=List[Todo])
async def get_todos():
    """Get all todos from database - returns a list of all todos"""
    # Call our database function and return the results
    return await get_todos_from_db()

# GET ONE TODO - GET /todos/{todo_id}
@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: str):
    """Get a specific todo by ID from database"""
    # {todo_id} in the URL becomes the todo_id parameter
    todo = await get_todo_from_db(todo_id)
    
    # If todo doesn't exist, return 404 error
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo

# CREATE NEW TODO - POST /todos
@app.post("/todos", response_model=Todo)
async def create_todo(todo: TodoCreate):
    """Create a new todo in database"""
    # The todo parameter automatically validates the request body against TodoCreate model
    # FastAPI automatically converts JSON to TodoCreate object
    return await create_todo_in_db(todo)

# UPDATE TODO - PUT /todos/{todo_id}
@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, todo_update: TodoCreate):
    """Update an existing todo in database"""
    # todo_id comes from URL path, todo_update comes from request body
    updated_todo = await update_todo_in_db(todo_id, todo_update)
    
    # If todo doesn't exist, return 404 error
    if not updated_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return updated_todo

# DELETE TODO - DELETE /todos/{todo_id}
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a todo from database"""
    # Try to delete the todo
    success = await delete_todo_from_db(todo_id)
    
    # If todo doesn't exist, return 404 error
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Return success message
    return {"message": "Todo deleted successfully"}

# HEALTH CHECK ENDPOINT - GET /health
@app.get("/health")
async def health_check():
    """Health check endpoint - used to verify if the API is running properly"""
    # Simple endpoint that returns a status - useful for monitoring tools
    return {"status": "healthy"}

# DIRECT EXECUTION (if you run this file directly with python main.py)
if __name__ == "__main__":
    import uvicorn
    # Start the server manually (we usually use uvicorn command instead)
    uvicorn.run(app, host="0.0.0.0", port=8000)