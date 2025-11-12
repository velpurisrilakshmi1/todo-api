"""
Test script for authentication endpoints
Run this to test registration and login functionality
"""
import asyncio
import aiosqlite
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("🧪 Testing User Registration...")
    
    # Test data
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123"
    }
    
    # Make registration request
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    
    if response.status_code == 200:
        print("✅ Registration successful!")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_login():
    """Test user login"""
    print("\n🧪 Testing User Login...")
    
    # Login data (same as registration)
    login_data = {
        "username": "testuser",
        "email": "testuser@example.com",  # email not used for login but required by model
        "password": "testpassword123"
    }
    
    # Make login request
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ Login successful!")
        token_data = response.json()
        print(f"Token received: {token_data['access_token'][:50]}...")
        return token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint"""
    print("\n🧪 Testing Protected Endpoint...")
    
    # Headers with JWT token
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Try to access todos (will be protected soon)
    response = requests.get(f"{BASE_URL}/todos", headers=headers)
    
    print(f"Todos endpoint status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Protected endpoint accessible!")
    else:
        print("⚠️ Todos endpoint not yet protected (that's next step)")

async def view_database():
    """View users in database"""
    print("\n📊 Users in Database:")
    try:
        async with aiosqlite.connect("todos.db") as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT id, username, email, created_at FROM users')
            rows = await cursor.fetchall()
            
            if not rows:
                print("No users found")
            else:
                for row in rows:
                    print(f"👤 {row['username']} ({row['email']}) - ID: {row['id'][:8]}...")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    print("🚀 Authentication System Test")
    print("=" * 40)
    
    # Test registration
    registration_success = test_registration()
    
    if registration_success:
        # Test login
        token = test_login()
        
        if token:
            # Test protected endpoint (when implemented)
            test_protected_endpoint(token)
    
    # View database
    asyncio.run(view_database())
    
    print("\n🎯 Test Complete!")