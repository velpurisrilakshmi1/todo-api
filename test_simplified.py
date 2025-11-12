"""
Simplified version of main.py to test middleware issues
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import uuid
import aiosqlite
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging

# Import configuration
from config import settings, validate_settings
from logging_config import setup_logging, get_logger

# Setup logging system
setup_logging()
app_start_time = datetime.utcnow()

# Validate configuration
validate_settings()
logger = get_logger("todo_api")

# Database path
DATABASE_PATH = "todos.db"

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool
    user_id: str

# Database functions
async def init_database():
    """Initialize the database with required tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create todos table with user_id for user isolation
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle"""
    await init_database()
    print(f"📄 Database initialized: {DATABASE_PATH}")
    yield

# Create FastAPI app
app = FastAPI(
    title="Todo API (Simplified)",
    description="A simple todo API for testing",
    version="1.0.0",
    lifespan=lifespan
)

# Basic endpoints
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {"message": "Welcome to Todo API (Simplified Version)"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": "development",
        "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds(),
        "message": "Todo API is running (simplified)"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"status": "working", "message": "Simplified API is functioning"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)