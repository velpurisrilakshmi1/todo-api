# User Authentication Implementation Guide

## 🔐 **Adding User Authentication to FastAPI Todo API**

### **What We'll Build:**
- User registration and login
- JWT (JSON Web Token) authentication
- Protected routes (only authenticated users can access their todos)
- Password hashing for security
- User-specific todos (each user sees only their own todos)

---

## 📋 **Step-by-Step Implementation Plan**

### 🎯 **Phase 1: Basic Setup**
1. **Install Authentication Dependencies**
2. **Create User Models** (Pydantic schemas)
3. **Update Database Schema** (add users table)
4. **Add Password Hashing Utilities**

### 🎯 **Phase 2: Authentication Logic**
5. **Create User Registration Endpoint**
6. **Create Login Endpoint** (returns JWT token)
7. **Create JWT Token Utilities**
8. **Add Authentication Dependency**

### 🎯 **Phase 3: Protect Todo Routes**
9. **Update Todo Model** (add user_id foreign key)
10. **Update Database Functions** (filter by user)
11. **Protect All Todo Endpoints**
12. **Test the Complete System**

---

## 🛠️ **Phase 1: Basic Setup**

### **1. Install Required Dependencies**

Add these to your `requirements.txt`:
```txt
# Existing dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
aiosqlite==0.19.0

# New authentication dependencies
python-jose[cryptography]==3.3.0  # JWT token handling
passlib[bcrypt]==1.7.4            # Password hashing
python-multipart==0.0.6           # Form data parsing
```

### **2. User Models (Pydantic Schemas)**

Add to your `main.py`:
```python
# User Models for Authentication
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: str

class User(UserBase):
    id: str
    hashed_password: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
```

### **3. Database Schema Updates**

Add users table and modify todos table:
```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Updated todos table (add user_id foreign key)
CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

---

## 🔒 **Phase 2: Authentication Logic**

### **4. Password Hashing & JWT Utilities**

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-here"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### **5. User Database Functions**

```python
async def create_user_in_db(user: UserCreate) -> User:
    """Create a new user in database"""
    # Check if user already exists
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        created_at=datetime.utcnow().isoformat()
    )
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, username, email, hashed_password) VALUES (?, ?, ?, ?)",
            (new_user.id, new_user.username, new_user.email, new_user.hashed_password)
        )
        await db.commit()
    
    return new_user

async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        row = await cursor.fetchone()
        return User(**dict(row)) if row else None

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

---

## 🛡️ **Phase 3: Protected Routes**

### **6. Authentication Dependency**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
```

### **7. Authentication Endpoints**

```python
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user"""
    db_user = await create_user_in_db(user)
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at
    )

@app.post("/login", response_model=Token)
async def login(form_data: UserCreate):
    """Login user and return JWT token"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### **8. Protected Todo Endpoints**

```python
# Update Todo model to include user_id
class Todo(TodoBase):
    id: str
    user_id: str  # Add this field

# Protected endpoints (add current_user parameter)
@app.get("/todos", response_model=List[Todo])
async def get_todos(current_user: User = Depends(get_current_user)):
    """Get all todos for the authenticated user"""
    return await get_user_todos_from_db(current_user.id)

@app.post("/todos", response_model=Todo)
async def create_todo(todo: TodoCreate, current_user: User = Depends(get_current_user)):
    """Create a new todo for the authenticated user"""
    return await create_todo_in_db(todo, current_user.id)

# Similar updates for PUT, DELETE endpoints...
```

---

## 🧪 **Testing the Authentication**

### **1. Register a User**
```bash
POST /register
{
  "username": "john_doe",
  "email": "john@example.com", 
  "password": "securepassword123"
}
```

### **2. Login to Get Token**
```bash
POST /login
{
  "username": "john_doe",
  "password": "securepassword123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### **3. Access Protected Routes**
```bash
GET /todos
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🎯 **Next Steps After Implementation**

1. **Environment Variables** - Move SECRET_KEY to environment variables
2. **Token Refresh** - Add refresh token functionality  
3. **Role-Based Access** - Add admin/user roles
4. **Email Verification** - Verify email addresses
5. **Password Reset** - Add forgot password functionality
6. **Rate Limiting** - Prevent brute force attacks

---

## 🚀 **Benefits of This Implementation**

✅ **Security**: Passwords are hashed, not stored in plain text
✅ **Scalable**: JWT tokens are stateless
✅ **User Isolation**: Each user sees only their own todos
✅ **Industry Standard**: Uses JWT, a widely adopted standard
✅ **Flexible**: Easy to extend with roles and permissions

Would you like me to help you implement any specific phase of this authentication system?