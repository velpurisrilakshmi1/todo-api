# Todo API Project - Workflow Diagram & Architecture

## 🏗️ **Overall Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser/Postman/etc.)               │
│                              📱💻🌐                                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ HTTP Requests (JSON)
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER                             │
│                      (main.py - Port 8000)                         │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   ENDPOINTS   │  │    MODELS    │  │    DATABASE FUNCTIONS   │  │
│  │   (Routes)    │  │  (Pydantic)  │  │     (CRUD Operations)   │  │
│  │               │  │              │  │                         │  │
│  │ GET /todos    │  │ TodoBase     │  │ get_todos_from_db()     │  │
│  │ POST /todos   │  │ TodoCreate   │  │ create_todo_in_db()     │  │
│  │ PUT /todos/:id │  │ Todo         │  │ update_todo_in_db()     │  │
│  │ DELETE /todos │  │              │  │ delete_todo_from_db()   │  │
│  └───────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ SQL Queries
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SQLITE DATABASE                              │
│                        (todos.db file)                             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    TODOS TABLE                              │  │
│  │ ┌────────┬─────────┬─────────────┬───────────┬─────────────┐ │  │
│  │ │   ID   │  TITLE  │ DESCRIPTION │ COMPLETED │ CREATED_AT  │ │  │
│  │ ├────────┼─────────┼─────────────┼───────────┼─────────────┤ │  │
│  │ │ uuid-1 │ Learn   │ Study APIs  │   FALSE   │ 2025-11-12  │ │  │
│  │ │ uuid-2 │ Code    │ Build app   │   TRUE    │ 2025-11-12  │ │  │
│  │ └────────┴─────────┴─────────────┴───────────┴─────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 **Request Flow Workflow**

### **1. CREATE TODO (POST /todos)**

```
CLIENT                    FASTAPI SERVER                   DATABASE
  │                           │                              │
  │ 1. POST /todos           │                              │
  │ {"title": "Learn FastAPI"} │                            │
  ├──────────────────────────►│                              │
  │                           │ 2. Validate with TodoCreate │
  │                           │    model                     │
  │                           │                              │
  │                           │ 3. Generate UUID             │
  │                           │    Create Todo object        │
  │                           │                              │
  │                           │ 4. SQL INSERT               │
  │                           ├─────────────────────────────►│
  │                           │                              │ 5. Store in
  │                           │                              │    todos table
  │                           │ 6. Confirm success          │
  │                           │◄─────────────────────────────┤
  │                           │                              │
  │ 7. Return created Todo    │                              │
  │◄──────────────────────────┤                              │
  │ {"id": "abc-123",         │                              │
  │  "title": "Learn FastAPI"} │                              │
```

### **2. GET ALL TODOS (GET /todos)**

```
CLIENT                    FASTAPI SERVER                   DATABASE
  │                           │                              │
  │ 1. GET /todos            │                              │
  ├──────────────────────────►│                              │
  │                           │ 2. Call get_todos_from_db()  │
  │                           │                              │
  │                           │ 3. SQL SELECT * FROM todos  │
  │                           ├─────────────────────────────►│
  │                           │                              │ 4. Query all
  │                           │                              │    todos
  │                           │ 5. Return rows               │
  │                           │◄─────────────────────────────┤
  │                           │                              │
  │                           │ 6. Convert to Todo objects   │
  │                           │                              │
  │ 7. Return JSON array      │                              │
  │◄──────────────────────────┤                              │
  │ [{"id": "abc-123", ...},  │                              │
  │  {"id": "def-456", ...}]  │                              │
```

### **3. UPDATE TODO (PUT /todos/{id})**

```
CLIENT                    FASTAPI SERVER                   DATABASE
  │                           │                              │
  │ 1. PUT /todos/abc-123    │                              │
  │ {"title": "Updated",      │                              │
  │  "completed": true}       │                              │
  ├──────────────────────────►│                              │
  │                           │ 2. Validate with TodoCreate │
  │                           │    Extract todo_id from URL │
  │                           │                              │
  │                           │ 3. SQL UPDATE WHERE id=?    │
  │                           ├─────────────────────────────►│
  │                           │                              │ 4. Update row
  │                           │                              │    if exists
  │                           │ 5. Return rowcount          │
  │                           │◄─────────────────────────────┤
  │                           │                              │
  │                           │ 6. Check if updated (rowcount > 0) │
  │                           │    If not: HTTP 404          │
  │                           │    If yes: return Todo       │
  │                           │                              │
  │ 7. Return updated Todo    │                              │
  │◄──────────────────────────┤                              │
  │ {"id": "abc-123",         │                              │
  │  "completed": true, ...}  │                              │
```

### **4. DELETE TODO (DELETE /todos/{id})**

```
CLIENT                    FASTAPI SERVER                   DATABASE
  │                           │                              │
  │ 1. DELETE /todos/abc-123 │                              │
  ├──────────────────────────►│                              │
  │                           │ 2. Extract todo_id from URL │
  │                           │                              │
  │                           │ 3. SQL DELETE WHERE id=?    │
  │                           ├─────────────────────────────►│
  │                           │                              │ 4. Delete row
  │                           │                              │    if exists
  │                           │ 5. Return rowcount          │
  │                           │◄─────────────────────────────┤
  │                           │                              │
  │                           │ 6. Check if deleted (rowcount > 0) │
  │                           │    If not: HTTP 404          │
  │                           │    If yes: success message   │
  │                           │                              │
  │ 7. Return success         │                              │
  │◄──────────────────────────┤                              │
  │ {"message": "Todo deleted │                              │
  │  successfully"}           │                              │
```

## 🔧 **Application Startup Flow**

```
1. 📁 PYTHON STARTS
   │
   ▼
2. 📚 IMPORT LIBRARIES
   │ - FastAPI, Pydantic, aiosqlite, uuid
   │
   ▼
3. 🏗️ DEFINE MODELS
   │ - TodoBase, TodoCreate, Todo
   │
   ▼
4. 📝 DEFINE DATABASE FUNCTIONS
   │ - init_database(), get_todos_from_db(), etc.
   │
   ▼
5. 🚀 CREATE FASTAPI APP
   │ - app = FastAPI(lifespan=lifespan)
   │
   ▼
6. 🔄 LIFESPAN STARTUP
   │ - await init_database()
   │ - CREATE TABLE IF NOT EXISTS todos
   │
   ▼
7. 📡 DEFINE ROUTES
   │ - @app.get("/todos")
   │ - @app.post("/todos")
   │ - @app.put("/todos/{todo_id}")
   │ - @app.delete("/todos/{todo_id}")
   │
   ▼
8. 🌐 START SERVER
   │ - Uvicorn starts on http://0.0.0.0:8000
   │ - Server ready to accept requests
```

## 📊 **Data Flow Through Models**

```
INCOMING REQUEST                PYDANTIC VALIDATION             DATABASE STORAGE
─────────────────              ───────────────────             ────────────────

JSON from client              TodoCreate model                 SQLite todos table
{                              ├─ title: str (required)        ├─ id TEXT PRIMARY KEY
  "title": "Learn",            ├─ description: str|None        ├─ title TEXT NOT NULL  
  "description": "Study",      └─ completed: bool = False      ├─ description TEXT
  "completed": false                                            ├─ completed BOOLEAN
}                                       │                      └─ created_at TIMESTAMP
        │                              │                               │
        └──────────────────────────────┼───────────────────────────────┘
                                       ▼
                              Todo model (with ID)
                              ├─ id: str (UUID generated)
                              ├─ title: str
                              ├─ description: str|None
                              └─ completed: bool

OUTGOING RESPONSE
─────────────────
JSON to client
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Learn",
  "description": "Study", 
  "completed": false
}
```

## 🛠️ **File Structure & Responsibilities**

```
📁 TODO/
├── 📄 main.py              ← Main application file
│   ├── 🏗️ Models (TodoBase, TodoCreate, Todo)
│   ├── 🗄️ Database functions (CRUD operations)
│   ├── 📡 API endpoints (routes)
│   └── 🚀 App initialization
│
├── 📄 requirements.txt     ← Dependencies list
├── 📄 README.md           ← Documentation
├── 📄 view_todos.py       ← Database viewer utility
├── 📁 .vscode/            ← VS Code configuration
│   └── tasks.json         ← Task to run server
└── 📁 .github/            ← GitHub configuration
    └── copilot-instructions.md
```

## 🔍 **Error Handling Flow**

```
REQUEST → FASTAPI → DATABASE → RESPONSE

Error Scenarios:

1. INVALID JSON
   Client → FastAPI: Invalid JSON
   FastAPI → Client: 422 Validation Error

2. TODO NOT FOUND
   Client → FastAPI → Database: SELECT WHERE id=?
   Database → FastAPI: No rows returned
   FastAPI → Client: 404 Not Found

3. DATABASE ERROR
   Client → FastAPI → Database: Connection fails
   Database → FastAPI: Exception thrown
   FastAPI → Client: 500 Internal Server Error
```

This workflow diagram shows you exactly how data flows through your FastAPI Todo application, making it easier to understand and debug! 🎯