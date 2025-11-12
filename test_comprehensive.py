"""
Comprehensive test suite for Todo API
Tests authentication, CRUD operations, validation, and security
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sqlite3
import os
from unittest.mock import patch

# Import the main application
from main import app
from config import settings

# Test configuration
TEST_DATABASE = "test_todos.db"
TEST_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

TEST_USER_DATA_2 = {
    "username": "testuser2", 
    "email": "test2@example.com",
    "password": "testpass456"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Create async test client"""
    # Use test database
    with patch('main.DATABASE_PATH', TEST_DATABASE):
        # Initialize test database manually
        import aiosqlite
        async with aiosqlite.connect(TEST_DATABASE) as db:
            # Create users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create todos table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_todos_user_id ON todos(user_id)")
            await db.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    # Cleanup test database
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

@pytest.fixture
def client():
    """Create sync test client for simple tests"""
    with patch('main.DATABASE_PATH', TEST_DATABASE):
        with TestClient(app) as client:
            yield client
    
    # Cleanup test database
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert "welcome" in response.json()["message"].lower()
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestUserAuthentication:
    """Test user registration and authentication"""
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, async_client):
        """Test successful user registration"""
        response = await async_client.post("/register", json=TEST_USER_DATA)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == TEST_USER_DATA["username"]
        assert data["email"] == TEST_USER_DATA["email"]
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio 
    async def test_user_registration_duplicate_username(self, async_client):
        """Test registration with duplicate username fails"""
        # Register first user
        await async_client.post("/register", json=TEST_USER_DATA)
        
        # Try to register with same username
        duplicate_user = {
            "username": TEST_USER_DATA["username"],
            "email": "different@example.com",
            "password": "different123"
        }
        response = await async_client.post("/register", json=duplicate_user)
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, async_client):
        """Test registration with duplicate email fails"""
        # Register first user
        await async_client.post("/register", json=TEST_USER_DATA)
        
        # Try to register with same email
        duplicate_user = {
            "username": "differentuser",  
            "email": TEST_USER_DATA["email"],
            "password": "different123"
        }
        response = await async_client.post("/register", json=duplicate_user)
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, async_client):
        """Test successful user login"""
        # Register user first
        await async_client.post("/register", json=TEST_USER_DATA)
        
        # Login
        login_data = {
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        }
        response = await async_client.post("/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials fails"""
        # Register user first
        await async_client.post("/register", json=TEST_USER_DATA)
        
        # Try login with wrong password
        login_data = {
            "username": TEST_USER_DATA["username"],
            "password": "wrongpassword"
        }
        response = await async_client.post("/login", json=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_login_nonexistent_user(self, async_client):
        """Test login with non-existent user fails"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = await async_client.post("/login", json=login_data)
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation and security"""
    
    @pytest.mark.asyncio
    async def test_password_too_short(self, async_client):
        """Test password length validation"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "123"  # Too short
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "password must be at least" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_password_no_number(self, async_client):
        """Test password must contain number"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "passwordonly"  # No number
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "number" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_password_no_letter(self, async_client):
        """Test password must contain letter"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345678"  # No letters
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "letter" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_email_format(self, async_client):
        """Test email format validation"""
        user_data = {
            "username": "testuser",
            "email": "invalidemail",  # Invalid format
            "password": "validpass123"
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_username_too_short(self, async_client):
        """Test username length validation"""
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "validpass123"
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "username must be at least" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_username_invalid_characters(self, async_client):
        """Test username character validation"""
        user_data = {
            "username": "test@user",  # Invalid characters
            "email": "test@example.com", 
            "password": "validpass123"
        }
        response = await async_client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "letters, numbers, and underscores" in response.json()["detail"].lower()


class TestTodoOperations:
    """Test todo CRUD operations with authentication"""
    
    async def get_auth_headers(self, client):
        """Helper function to get authentication headers"""
        # Register and login user
        await client.post("/register", json=TEST_USER_DATA)
        
        login_response = await client.post("/login", json={
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_create_todo_success(self, async_client):
        """Test successful todo creation"""
        headers = await self.get_auth_headers(async_client)
        
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description",
            "completed": False
        }
        
        response = await async_client.post("/todos", json=todo_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["completed"] == False
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_todo_unauthorized(self, async_client):
        """Test todo creation without authentication fails"""
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description", 
            "completed": False
        }
        
        response = await async_client.post("/todos", json=todo_data)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_todos_success(self, async_client):
        """Test getting user's todos"""
        headers = await self.get_auth_headers(async_client)
        
        # Create a todo first
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description",
            "completed": False
        }
        await async_client.post("/todos", json=todo_data, headers=headers)
        
        # Get todos
        response = await async_client.get("/todos", headers=headers)
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]["title"] == todo_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_todos_unauthorized(self, async_client):
        """Test getting todos without authentication fails"""
        response = await async_client.get("/todos")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, async_client):
        """Test that users can only see their own todos"""
        # Register and create todo for first user
        headers1 = await self.get_auth_headers(async_client)
        
        todo_data1 = {
            "title": "User 1 Todo",
            "description": "Description 1",
            "completed": False
        }
        await async_client.post("/todos", json=todo_data1, headers=headers1)
        
        # Register second user  
        await async_client.post("/register", json=TEST_USER_DATA_2)
        login_response = await async_client.post("/login", json={
            "username": TEST_USER_DATA_2["username"],
            "password": TEST_USER_DATA_2["password"]
        })
        token2 = login_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create todo for second user
        todo_data2 = {
            "title": "User 2 Todo", 
            "description": "Description 2",
            "completed": False
        }
        await async_client.post("/todos", json=todo_data2, headers=headers2)
        
        # Each user should only see their own todos
        response1 = await async_client.get("/todos", headers=headers1)
        todos1 = response1.json()
        assert len(todos1) == 1
        assert todos1[0]["title"] == "User 1 Todo"
        
        response2 = await async_client.get("/todos", headers=headers2)
        todos2 = response2.json()
        assert len(todos2) == 1
        assert todos2[0]["title"] == "User 2 Todo"
    
    @pytest.mark.asyncio
    async def test_update_todo_success(self, async_client):
        """Test successful todo update"""
        headers = await self.get_auth_headers(async_client)
        
        # Create todo
        todo_data = {
            "title": "Original Title",
            "description": "Original Description",
            "completed": False
        }
        create_response = await async_client.post("/todos", json=todo_data, headers=headers)
        todo_id = create_response.json()["id"]
        
        # Update todo
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description", 
            "completed": True
        }
        response = await async_client.put(f"/todos/{todo_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["completed"] == True
    
    @pytest.mark.asyncio
    async def test_delete_todo_success(self, async_client):
        """Test successful todo deletion"""
        headers = await self.get_auth_headers(async_client)
        
        # Create todo
        todo_data = {
            "title": "To Be Deleted",
            "description": "This will be deleted",
            "completed": False
        }
        create_response = await async_client.post("/todos", json=todo_data, headers=headers)
        todo_id = create_response.json()["id"]
        
        # Delete todo
        response = await async_client.delete(f"/todos/{todo_id}", headers=headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        
        # Verify todo is gone
        get_response = await async_client.get(f"/todos/{todo_id}", headers=headers)
        assert get_response.status_code == 404


class TestJWTSecurity:
    """Test JWT token security"""
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, async_client):
        """Test that invalid tokens are rejected"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await async_client.get("/todos", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_token(self, async_client):
        """Test that malformed tokens are rejected"""
        headers = {"Authorization": "Bearer"}  # No token
        
        response = await async_client.get("/todos", headers=headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, async_client):
        """Test that missing authorization header is rejected"""
        response = await async_client.get("/todos")
        assert response.status_code == 403


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_nonexistent_todo(self, async_client):
        """Test accessing non-existent todo returns 404"""
        # Register and login
        await async_client.post("/register", json=TEST_USER_DATA)
        login_response = await async_client.post("/login", json={
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get non-existent todo
        response = await async_client.get("/todos/nonexistent-id", headers=headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invalid_todo_data(self, async_client):
        """Test creating todo with invalid data"""
        # Register and login
        await async_client.post("/register", json=TEST_USER_DATA)
        login_response = await async_client.post("/login", json={
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to create todo without required title
        invalid_todo = {
            "description": "Description without title",
            "completed": False
        }
        
        response = await async_client.post("/todos", json=invalid_todo, headers=headers)
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])