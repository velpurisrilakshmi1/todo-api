"""
DATABASE VIEWER SCRIPT
======================
Simple script to view todos stored in SQLite database
Run this script to see all todos in your database

Usage: python view_todos.py
"""

# Import necessary libraries
import asyncio      # For running async functions
import aiosqlite    # For async SQLite database operations

# Database configuration (must match main.py)
DATABASE_PATH = "todos.db"

async def view_todos():
    """View all todos in the database with nice formatting"""
    try:
        # Connect to the same database that main.py uses
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Set row_factory to access columns by name (like a dictionary)
            db.row_factory = aiosqlite.Row
            
            # Get all todos from database, newest first
            cursor = await db.execute('SELECT * FROM todos ORDER BY created_at DESC')
            rows = await cursor.fetchall()
            
            # Check if we have any todos
            if not rows:
                print("📝 No todos found in database")
                return
            
            # Display header
            print("📝 Todos in Database:")
            print("-" * 60)
            
            # Loop through each todo and display it nicely
            for row in rows:
                # Show different emoji based on completion status
                status = "✅" if row['completed'] else "⏳"
                
                # Display todo information
                print(f"{status} {row['title']}")                    # Title with status emoji
                
                if row['description']:                               # Only show description if it exists
                    print(f"   📄 {row['description']}")
                
                print(f"   🆔 ID: {row['id']}")                      # Unique identifier
                print(f"   📅 Created: {row['created_at']}")          # When it was created
                print("-" * 60)                                      # Separator line
                
    except Exception as e:
        # Handle any errors (database doesn't exist, permissions, etc.)
        print(f"❌ Error reading database: {e}")

# Run the script when executed directly (not imported)
if __name__ == "__main__":
    # asyncio.run() is needed to run async functions from a regular Python script
    asyncio.run(view_todos())