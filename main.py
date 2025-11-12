# Import necessary libraries for our FastAPI application
from fastapi import FastAPI, HTTPException, Depends, status  # FastAPI framework and HTTP exception handling
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # For JWT authentication
from fastapi.middleware.cors import CORSMiddleware  # For CORS handling
from pydantic import BaseModel              # For data validation and serialization
from typing import List, Optional           # Type hints for better code readability
import uuid                                 # Generate unique IDs for todos
import aiosqlite                           # Async SQLite database operations
import os                                  # Operating system interface
from contextlib import asynccontextmanager  # For managing application startup/shutdown
from datetime import datetime, timedelta   # For JWT token expiration
from passlib.context import CryptContext   # For password hashing
from jose import JWTError, jwt             # For JWT token creation and verification
import logging                             # For application logging
import re                                  # For regex pattern matching

# Import configuration
from config import settings, validate_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
validate_settings()

# Database configuration
DATABASE_PATH = "todos.db"  # SQLite database file name (will be created automatically)

# Password hashing configuration using settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()

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
    id: str      # Unique identifier - added when todo is saved to database
    user_id: str # Links this todo to a specific user

# USER AUTHENTICATION MODELS
# These models handle user registration, login, and JWT tokens

class UserBase(BaseModel):
    """Base user model with common fields"""
    username: str                        # Unique username for login
    email: str                          # User's email address

class UserCreate(UserBase):
    """Model for user registration (includes password)"""
    password: str                       # Plain text password (will be hashed before storing)

class UserLogin(BaseModel):
    """Model for user login (username and password only)"""
    username: str                       # Username for login
    password: str                       # Password for login

class UserResponse(UserBase):
    """Model for user data in API responses (no password!)"""
    id: str                            # Unique user identifier
    created_at: str                    # When the user account was created

class User(UserBase):
    """Complete user model for internal use (includes hashed password)"""
    id: str                            # Unique user identifier  
    hashed_password: str               # Securely hashed password
    created_at: str                    # When the user account was created

class Token(BaseModel):
    """JWT token response model"""
    access_token: str                  # The JWT token string
    token_type: str                    # Always "bearer" for JWT

class TokenData(BaseModel):
    """Data extracted from JWT token"""
    username: Optional[str] = None     # Username from token payload

# INPUT VALIDATION FUNCTIONS
def validate_password_strength(password: str) -> None:
    """Validate password meets security requirements"""
    if len(password) < settings.min_password_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.min_password_length} characters long"
        )
    
    # Check for at least one number
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    
    # Check for at least one letter
    if not re.search(r"[a-zA-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one letter"
        )

def validate_email_format(email: str) -> None:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

def validate_username(username: str) -> None:
    """Validate username format"""
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    if len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be less than 50 characters"
        )
    
    # Only allow alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can only contain letters, numbers, and underscores"
        )

# PASSWORD & JWT UTILITY FUNCTIONS
# These functions handle password hashing and JWT token operations

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    # Uses bcrypt to check if the plain password matches the hash
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt"""
    # Creates a secure hash that can't be reversed to get the original password
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    # Copy the data to avoid modifying the original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default 15 minutes
    
    # Add expiration to token payload
    to_encode.update({"exp": expire})
    
    # Create and return the JWT token
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

# DATABASE FUNCTIONS
# These functions handle all interactions with the SQLite database

async def init_database():
    """Initialize the database and create tables if they don't exist"""
    # Connect to SQLite database (creates file if it doesn't exist)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create the users table for authentication
        # - id: Unique identifier (PRIMARY KEY)
        # - username: Unique username for login (NOT NULL, UNIQUE)
        # - email: User's email address (NOT NULL, UNIQUE)  
        # - hashed_password: Securely hashed password (NOT NULL)
        # - created_at: When the account was created
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create the todos table with user relationship
        # - id: Unique identifier (PRIMARY KEY)
        # - title: Todo title (required, NOT NULL)
        # - description: Optional description
        # - completed: Boolean flag (defaults to FALSE)
        # - user_id: Links todo to a user (FOREIGN KEY, NOT NULL)
        # - created_at: Timestamp when todo was created
        await db.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # Save changes to the database
        await db.commit()

async def get_todos_from_db(user_id: str) -> List[Todo]:
    """Get all todos for a specific user from database - returns a list of Todo objects"""
    # Connect to database
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Set row_factory to access columns by name (like a dictionary)
        db.row_factory = aiosqlite.Row
        
        # Execute SQL query to get todos for specific user only, ordered by newest first
        cursor = await db.execute(
            'SELECT id, title, description, completed, user_id FROM todos WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        
        # Fetch all results from the query
        rows = await cursor.fetchall()
        
        # Convert database rows to Todo objects
        # **dict(row) unpacks the row dictionary as keyword arguments to Todo()
        return [Todo(**dict(row)) for row in rows]

async def get_todo_from_db(todo_id: str, user_id: str) -> Optional[Todo]:
    """Get a specific todo by ID for a specific user from database - returns Todo object or None if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Set row_factory to access columns by name
        db.row_factory = aiosqlite.Row
        
        # Execute SQL query with parameter substitution (? prevents SQL injection)
        # Check both todo_id AND user_id to ensure user can only access their own todos
        cursor = await db.execute(
            'SELECT id, title, description, completed, user_id FROM todos WHERE id = ? AND user_id = ?', 
            (todo_id, user_id)
        )
        
        # Fetch only one result (since ID should be unique)
        row = await cursor.fetchone()
        
        # Return Todo object if found, otherwise return None
        return Todo(**dict(row)) if row else None

async def create_todo_in_db(todo: TodoCreate, user_id: str) -> Todo:
    """Create a new todo for a specific user in database - returns the created Todo object"""
    # Create a new Todo object with a unique ID and link it to the user
    new_todo = Todo(
        id=str(uuid.uuid4()),              # Generate unique ID (UUID = Universal Unique Identifier)
        title=todo.title,                  # Copy title from input
        description=todo.description,      # Copy description from input
        completed=todo.completed,          # Copy completed status from input
        user_id=user_id                    # Link todo to the authenticated user
    )
    
    # Connect to database and insert the new todo
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # INSERT SQL statement with parameter substitution for security
        # Now includes user_id to link todo to specific user
        await db.execute(
            'INSERT INTO todos (id, title, description, completed, user_id) VALUES (?, ?, ?, ?, ?)',
            (new_todo.id, new_todo.title, new_todo.description, new_todo.completed, new_todo.user_id)
        )
        # Save changes to database
        await db.commit()
    
    # Return the created todo object
    return new_todo

async def update_todo_in_db(todo_id: str, todo_update: TodoCreate, user_id: str) -> Optional[Todo]:
    """Update a todo for a specific user in database - returns updated Todo object or None if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Execute UPDATE SQL statement
        # Check both todo_id AND user_id to ensure user can only update their own todos
        cursor = await db.execute(
            'UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ? AND user_id = ?',
            (todo_update.title, todo_update.description, todo_update.completed, todo_id, user_id)
        )
        # Save changes to database
        await db.commit()
        
        # Check if any row was actually updated
        # cursor.rowcount tells us how many rows were affected by the query
        if cursor.rowcount == 0:
            return None  # No todo found with that ID for this user
        
        # Return the updated todo object
        return Todo(
            id=todo_id,                            # Keep the same ID
            title=todo_update.title,               # New title
            description=todo_update.description,   # New description
            completed=todo_update.completed,       # New completed status
            user_id=user_id                        # Keep the user_id
        )

async def delete_todo_from_db(todo_id: str, user_id: str) -> bool:
    """Delete a todo for a specific user from database - returns True if deleted, False if not found"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Execute DELETE SQL statement
        # Check both todo_id AND user_id to ensure user can only delete their own todos
        cursor = await db.execute('DELETE FROM todos WHERE id = ? AND user_id = ?', (todo_id, user_id))
        # Save changes to database
        await db.commit()
        
        # Return True if a row was deleted, False if no todo was found with that ID for this user
        return cursor.rowcount > 0

# USER DATABASE FUNCTIONS
# These functions handle user registration, login, and authentication

async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username from database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Set row_factory to access columns by name
        db.row_factory = aiosqlite.Row
        
        # Query user by username
        cursor = await db.execute(
            'SELECT id, username, email, hashed_password, created_at FROM users WHERE username = ?', 
            (username,)
        )
        row = await cursor.fetchone()
        
        # Return User object if found, otherwise None
        return User(**dict(row)) if row else None

async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email from database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT id, username, email, hashed_password, created_at FROM users WHERE email = ?', 
            (email,)
        )
        row = await cursor.fetchone()
        return User(**dict(row)) if row else None

async def create_user_in_db(user: UserCreate) -> User:
    """Create a new user in database"""
    # Check if username already exists
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered"
        )
    
    # Hash the password for secure storage
    hashed_password = get_password_hash(user.password)
    
    # Create new user object
    new_user = User(
        id=str(uuid.uuid4()),                    # Generate unique ID
        username=user.username,                  # Username from request
        email=user.email,                        # Email from request
        hashed_password=hashed_password,         # Securely hashed password
        created_at=datetime.utcnow().isoformat() # Current timestamp
    )
    
    # Insert user into database
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT INTO users (id, username, email, hashed_password) VALUES (?, ?, ?, ?)',
            (new_user.id, new_user.username, new_user.email, new_user.hashed_password)
        )
        await db.commit()
    
    return new_user

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    # Get user from database
    user = await get_user_by_username(username)
    if not user:
        return None  # User not found
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        return None  # Wrong password
    
    return user  # Authentication successful

# JWT AUTHENTICATION DEPENDENCY
# This function extracts and validates JWT tokens from requests

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token"""
    # Define the exception to raise if authentication fails
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token to get the payload
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        
        # Extract username from token (stored in "sub" field)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Create token data object
        token_data = TokenData(username=username)
        
    except JWTError:
        # Token is invalid (expired, malformed, wrong signature)
        raise credentials_exception
    
    # Get user from database using username from token
    user = await get_user_by_username(username=token_data.username)
    if user is None:
        # User no longer exists in database
        raise credentials_exception
        
    return user  # Return authenticated user

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
    title=settings.api_title,                                   # API title from settings
    description=settings.api_description,                       # API description from settings
    version=settings.api_version,                               # API version from settings
    debug=settings.debug,                                       # Debug mode from settings
    lifespan=lifespan                                          # Attach startup/shutdown handler
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API ENDPOINTS (Routes)
# These are the URLs that clients can call to interact with our API

# ROOT ENDPOINT - GET /
@app.get("/")
async def root():
    """Welcome message - simple endpoint to test if API is working"""
    return {"message": "Welcome to Todo API with Authentication! 🔐🗄️"}

# AUTHENTICATION ENDPOINTS
# These endpoints handle user registration and login

# REGISTER NEW USER - POST /register
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user account with validation"""
    logger.info(f"Registration attempt for username: {user.username}")
    
    # Validate input data
    validate_username(user.username)
    validate_email_format(user.email)
    validate_password_strength(user.password)
    
    # Create user in database (will throw error if username/email exists)
    db_user = await create_user_in_db(user)
    
    logger.info(f"Successfully registered user: {user.username}")
    
    # Return user data (without password!) 
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at
    )

# USER LOGIN - POST /login
@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user and return JWT access token"""
    # Authenticate user with username and password
    user = await authenticate_user(user_credentials.username, user_credentials.password)
    
    # If authentication failed, return 401 Unauthorized
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},  # "sub" is standard JWT claim for subject (user)
        expires_delta=access_token_expires
    )
    
    # Return token for client to use in future requests
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# PROTECTED TODO ENDPOINTS
# These endpoints require authentication (JWT token) and return user-specific data

# GET ALL TODOS - GET /todos (Protected)
@app.get("/todos", response_model=List[Todo])
async def get_todos(current_user: User = Depends(get_current_user)):
    """Get all todos for the authenticated user from database"""
    # Call our database function with the authenticated user's ID
    # This ensures users only see their own todos
    return await get_todos_from_db(current_user.id)

# GET ONE TODO - GET /todos/{todo_id} (Protected)
@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific todo by ID for the authenticated user from database"""
    # {todo_id} in the URL becomes the todo_id parameter
    # Also pass user_id to ensure user can only access their own todos
    todo = await get_todo_from_db(todo_id, current_user.id)
    
    # If todo doesn't exist or doesn't belong to user, return 404 error
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo

# CREATE NEW TODO - POST /todos (Protected)
@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate, current_user: User = Depends(get_current_user)):
    """Create a new todo for the authenticated user in database"""
    # The todo parameter automatically validates the request body against TodoCreate model
    # FastAPI automatically converts JSON to TodoCreate object
    # Pass the authenticated user's ID to link the todo to this user
    return await create_todo_in_db(todo, current_user.id)

# UPDATE TODO - PUT /todos/{todo_id} (Protected)
@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, todo_update: TodoCreate, current_user: User = Depends(get_current_user)):
    """Update an existing todo for the authenticated user in database"""
    # todo_id comes from URL path, todo_update comes from request body
    # Pass user_id to ensure user can only update their own todos
    updated_todo = await update_todo_in_db(todo_id, todo_update, current_user.id)
    
    # If todo doesn't exist or doesn't belong to user, return 404 error
    if not updated_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return updated_todo

# DELETE TODO - DELETE /todos/{todo_id} (Protected)
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str, current_user: User = Depends(get_current_user)):
    """Delete a todo for the authenticated user from database"""
    # Try to delete the todo for this specific user
    success = await delete_todo_from_db(todo_id, current_user.id)
    
    # If todo doesn't exist or doesn't belong to user, return 404 error
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