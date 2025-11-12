# Testing Protected Todo Endpoints with Authentication

## 🔐 **Complete Testing Guide with Sample Requests & Responses**

### **Prerequisites: Get Your JWT Token**

First, you need to login to get a JWT token:

**Request:**
```bash
POST /login
Content-Type: application/json

{
  "username": "test",
  "email": "test@gmail.com",
  "password": "test"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNzYyOTcwOTY2fQ.qH6x_wxdTKh8m0-F2iHDAIr_u_Qoo_EQyUKuNYeVI1Q",
  "token_type": "bearer"
}
```

**📝 Copy this token - you'll need it for all todo requests!**

---

## 🧪 **Testing All Protected Endpoints**

### **1. CREATE TODO - POST /todos**

**Request:**
```bash
POST /todos
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNzYyOTcwOTY2fQ.qH6x_wxdTKh8m0-F2iHDAIr_u_Qoo_EQyUKuNYeVI1Q
Content-Type: application/json

{
  "title": "Learn FastAPI Authentication",
  "description": "Master JWT tokens and user-specific data",
  "completed": false
}
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Learn FastAPI Authentication",
  "description": "Master JWT tokens and user-specific data",
  "completed": false,
  "user_id": "user-uuid-here"
}
```

**Status Code:** `200 OK`

---

### **2. CREATE ANOTHER TODO**

**Request:**
```bash
POST /todos
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "title": "Build a REST API",
  "description": "Complete todo API with authentication",
  "completed": true
}
```

**Expected Response:**
```json
{
  "id": "different-uuid-here",
  "title": "Build a REST API", 
  "description": "Complete todo API with authentication",
  "completed": true,
  "user_id": "same-user-uuid"
}
```

---

### **3. GET ALL TODOS - GET /todos**

**Request:**
```bash
GET /todos
Authorization: Bearer YOUR_TOKEN_HERE
```

**Expected Response:**
```json
[
  {
    "id": "different-uuid-here",
    "title": "Build a REST API",
    "description": "Complete todo API with authentication", 
    "completed": true,
    "user_id": "your-user-uuid"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Learn FastAPI Authentication",
    "description": "Master JWT tokens and user-specific data",
    "completed": false,
    "user_id": "your-user-uuid"
  }
]
```

**Status Code:** `200 OK`

**Note:** Only returns todos belonging to the authenticated user!

---

### **4. GET SPECIFIC TODO - GET /todos/{id}**

**Request:**
```bash
GET /todos/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer YOUR_TOKEN_HERE
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Learn FastAPI Authentication",
  "description": "Master JWT tokens and user-specific data",
  "completed": false,
  "user_id": "your-user-uuid"
}
```

**Status Code:** `200 OK`

---

### **5. UPDATE TODO - PUT /todos/{id}**

**Request:**
```bash
PUT /todos/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "title": "Learn FastAPI Authentication",
  "description": "Completed! Now I understand JWT tokens",
  "completed": true
}
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Learn FastAPI Authentication",
  "description": "Completed! Now I understand JWT tokens",
  "completed": true,
  "user_id": "your-user-uuid"
}
```

**Status Code:** `200 OK`

---

### **6. DELETE TODO - DELETE /todos/{id}**

**Request:**
```bash
DELETE /todos/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer YOUR_TOKEN_HERE
```

**Expected Response:**
```json
{
  "message": "Todo deleted successfully"
}
```

**Status Code:** `200 OK`

---

## ❌ **Error Scenarios**

### **1. Missing Authentication Token**

**Request:**
```bash
GET /todos
# No Authorization header
```

**Error Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Status Code:** `403 Forbidden`

---

### **2. Invalid/Expired Token**

**Request:**
```bash
GET /todos
Authorization: Bearer invalid-token-here
```

**Error Response:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Status Code:** `401 Unauthorized`

---

### **3. Todo Not Found (or belongs to another user)**

**Request:**
```bash
GET /todos/non-existent-id
Authorization: Bearer YOUR_VALID_TOKEN
```

**Error Response:**
```json
{
  "detail": "Todo not found"
}
```

**Status Code:** `404 Not Found`

---

## 🎯 **Testing in FastAPI Docs (Swagger UI)**

### **Step 1: Login and Get Token**
1. Go to http://localhost:8000/docs
2. Find `POST /login` endpoint
3. Click "Try it out"
4. Enter your credentials:
   ```json
   {
     "username": "test",
     "email": "test@gmail.com", 
     "password": "test"
   }
   ```
5. Click "Execute"
6. **Copy the access_token from the response**

### **Step 2: Authorize All Requests**
1. Click the **🔒 Authorize** button at the top of the page
2. In the "HTTPBearer" field, enter: `Bearer YOUR_TOKEN_HERE`
   - Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3. Click "Authorize"
4. Click "Close"

### **Step 3: Test Protected Endpoints**
Now all your requests will include the authentication token automatically!

1. **Create Todo:** POST /todos
2. **Get All Todos:** GET /todos  
3. **Get Specific Todo:** GET /todos/{id}
4. **Update Todo:** PUT /todos/{id}
5. **Delete Todo:** DELETE /todos/{id}

---

## 🧪 **Testing with cURL Commands**

Replace `YOUR_TOKEN_HERE` with your actual JWT token:

```bash
# Create todo
curl -X POST "http://localhost:8000/todos" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Todo",
    "description": "Testing authentication",
    "completed": false
  }'

# Get all todos
curl -X GET "http://localhost:8000/todos" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get specific todo (replace with actual ID)
curl -X GET "http://localhost:8000/todos/ACTUAL_TODO_ID" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Update todo (replace with actual ID)
curl -X PUT "http://localhost:8000/todos/ACTUAL_TODO_ID" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Todo",
    "description": "Updated via cURL",
    "completed": true
  }'

# Delete todo (replace with actual ID)
curl -X DELETE "http://localhost:8000/todos/ACTUAL_TODO_ID" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🔐 **Security Features Demonstrated**

1. **Token Required:** All todo endpoints require valid JWT token
2. **User Isolation:** Users can only see/modify their own todos
3. **Token Expiration:** Tokens expire after 30 minutes
4. **Secure Headers:** Uses standard Bearer token authentication
5. **Database Security:** User ID checked in all database queries

---

## 🎉 **What This Proves**

✅ **Authentication Works:** Only logged-in users can access todos
✅ **Authorization Works:** Users can only access their own data  
✅ **Security Works:** Invalid tokens are rejected
✅ **Isolation Works:** Each user has their own todo list
✅ **Production Ready:** Follows industry standards

Your FastAPI Todo API is now a **fully authenticated, multi-user application**! 🚀