# Simple Visual Flow - Todo API Operations

## 🎯 **Quick Reference: What Happens When You...**

### **CREATE a Todo (POST /todos)**
```
You send JSON → FastAPI validates → Generates ID → Saves to database → Returns Todo with ID
     ↓              ↓                    ↓              ↓                    ↓
{"title": "Learn"} → TodoCreate model → UUID generated → INSERT INTO todos → {"id": "abc", "title": "Learn"}
```

### **GET All Todos (GET /todos)**
```
You request → FastAPI queries database → Converts to objects → Returns JSON array
     ↓              ↓                          ↓                    ↓
GET /todos → SELECT * FROM todos → [Todo objects] → [{"id": "abc", ...}, {...}]
```

### **UPDATE a Todo (PUT /todos/abc-123)**
```
You send JSON + ID → FastAPI validates → Updates database → Returns updated Todo
        ↓                    ↓                  ↓                 ↓
PUT + {"completed": true} → TodoCreate → UPDATE WHERE id=abc → {"id": "abc", "completed": true}
```

### **DELETE a Todo (DELETE /todos/abc-123)**
```
You send DELETE request → FastAPI extracts ID → Deletes from database → Returns success message
          ↓                       ↓                    ↓                       ↓
    DELETE /todos/abc → Extract "abc" from URL → DELETE WHERE id=abc → {"message": "deleted"}
```

## 🔄 **Complete Request Lifecycle**

```
🌐 CLIENT BROWSER/APP
   │ 1. User clicks "Create Todo"
   │ 2. Frontend sends HTTP request
   ▼
📡 HTTP REQUEST
   │ POST /todos
   │ Content-Type: application/json
   │ Body: {"title": "Learn FastAPI", "description": "Study backend"}
   ▼
🚀 FASTAPI SERVER (main.py)
   │ 3. Route matching: @app.post("/todos")
   │ 4. Parameter extraction & validation
   │ 5. Call create_todo(todo: TodoCreate)
   ▼
✅ PYDANTIC VALIDATION
   │ 6. Validate JSON against TodoCreate model
   │ 7. Convert JSON to Python object
   │ 8. Check required fields, types, etc.
   ▼
🔧 BUSINESS LOGIC
   │ 9. Generate unique ID (UUID)
   │ 10. Create Todo object with ID
   │ 11. Call create_todo_in_db(todo)
   ▼
🗄️ DATABASE OPERATION
   │ 12. Connect to SQLite (todos.db)
   │ 13. Execute: INSERT INTO todos (id, title, description, completed) VALUES (?, ?, ?, ?)
   │ 14. Commit transaction
   │ 15. Close connection
   ▼
📤 RESPONSE GENERATION
   │ 16. Return Todo object
   │ 17. FastAPI converts to JSON
   │ 18. Set HTTP status code (201 Created)
   ▼
🌐 CLIENT RECEIVES
   │ 19. HTTP 201 Created
   │ 20. JSON: {"id": "550e8400-...", "title": "Learn FastAPI", ...}
   │ 21. Frontend updates UI
```

## 🧭 **Decision Points in Your API**

```
REQUEST COMES IN
       │
       ▼
┌─────────────────┐     NO      ┌──────────────────┐
│ Valid JSON?     ├─────────────►│ Return 422 Error │
└─────────┬───────┘             └──────────────────┘
          │ YES
          ▼
┌─────────────────┐     NO      ┌──────────────────┐
│ Valid Route?    ├─────────────►│ Return 404 Error │
└─────────┬───────┘             └──────────────────┘
          │ YES
          ▼
┌─────────────────┐
│ Which Operation?│
└─────────┬───────┘
          │
    ┌─────┼─────┬─────┬─────┐
    ▼     ▼     ▼     ▼     ▼
  CREATE READ UPDATE DELETE HEALTH
    │     │     │      │      │
    ▼     ▼     ▼      ▼      ▼
┌────────────────────────────────┐
│     DATABASE OPERATIONS        │
│  - Check if exists (for U/D)   │
│  - Execute SQL                  │
│  - Handle errors                │
└─────────────┬──────────────────┘
              ▼
         ┌─────────────┐    NO     ┌──────────────────┐
         │ Success?    ├───────────►│ Return Error     │
         └─────┬───────┘           │ (404, 500, etc.) │
               │ YES                └──────────────────┘
               ▼
    ┌─────────────────────┐
    │ Return Success      │
    │ with Data/Message   │
    └─────────────────────┘
```

## 📚 **Learning Path Through the Code**

```
START HERE (Beginner Path)
│
├── 1. 📄 README.md          ← Understand what the project does
│
├── 2. 🏗️ Models Section     ← Learn data structures
│   │   (TodoBase, TodoCreate, Todo)
│   │
├── 3. 📡 Simple Endpoints   ← Start with easy routes
│   │   GET / (root)
│   │   GET /health
│   │
├── 4. 📊 Database Basics    ← Understand persistence
│   │   init_database()
│   │   view_todos.py
│   │
├── 5. 🔄 CRUD Operations    ← Core functionality
│   │   CREATE: POST /todos
│   │   READ:   GET /todos, GET /todos/{id}
│   │   UPDATE: PUT /todos/{id}
│   │   DELETE: DELETE /todos/{id}
│   │
└── 6. 🚀 Advanced Concepts  ← Next level learning
    │   Error handling
    │   Async programming
    │   Database connections
    │   API documentation
```

## 🎮 **Try This Learning Exercise**

1. **Start the server**: `python -m uvicorn main:app --reload`
2. **Open docs**: http://localhost:8000/docs
3. **Follow this sequence**:
   ```
   Step 1: GET /todos         (should be empty initially)
   Step 2: POST /todos        (create your first todo)  
   Step 3: GET /todos         (see your todo in the list)
   Step 4: PUT /todos/{id}    (mark it as completed)
   Step 5: GET /todos/{id}    (verify the change)
   Step 6: DELETE /todos/{id} (remove the todo)
   Step 7: GET /todos         (should be empty again)
   ```
4. **Between each step**, run: `python view_todos.py` to see database changes!

This workflow diagram shows you the complete journey of data through your FastAPI application! 🎯✨