import pyodbc
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import time

# Database configuration - Update with your SOMEE credentials
DATABASE_CONFIG = {
    "server": "RecipeDB.mssql.somee.com",  # Replace with your SOMEE server
    "database": "RecipeDB",        # Replace with your database name
    "username": "ShiraAlk_SQLLogin_1",            # Replace with your username
    "password": "6nX2uN7f",            # Replace with your password
    "driver": "ODBC Driver 18 for SQL Server"
}

# Connection string (same as your working script)
CONNECTION_STRING = (
    f"DRIVER={{{DATABASE_CONFIG['driver']}}};"
    f"SERVER={DATABASE_CONFIG['server']};"
    f"DATABASE={DATABASE_CONFIG['database']};"
    f"UID={DATABASE_CONFIG['username']};"
    f"PWD={DATABASE_CONFIG['password']};"
    f"TrustServerCertificate=yes;"
    f"Encrypt=yes;"
)

# Thread-local storage for connections
thread_local = threading.local()

def get_connection():
    """
    Get a database connection for the current thread
    
    Returns:
        pyodbc.Connection: Database connection
    """
    if not hasattr(thread_local, "connection") or thread_local.connection is None:
        try:
            print("🔗 Creating new database connection...")
            thread_local.connection = pyodbc.connect(CONNECTION_STRING)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Failed to create database connection: {e}")
            raise
    
    return thread_local.connection

def close_connection():
    """
    Close the database connection for the current thread
    """
    if hasattr(thread_local, "connection") and thread_local.connection:
        try:
            thread_local.connection.close()
            print("🔒 Database connection closed")
        except Exception as e:
            print(f"⚠️ Error closing connection: {e}")
        finally:
            thread_local.connection = None

@contextmanager
def get_database_cursor():
    """
    Context manager for database operations
    
    Provides a cursor and handles connection management
    Automatically commits on success, rollbacks on error
    
    Usage:
        with get_database_cursor() as cursor:
            cursor.execute("SELECT * FROM Users")
            result = cursor.fetchall()
    
    Yields:
        pyodbc.Cursor: Database cursor
    """
    connection = None
    cursor = None
    
    try:
        connection = get_connection()
        cursor = connection.cursor()
        print("📋 Database cursor created")
        
        yield cursor
        
        # Commit the transaction if no errors occurred
        connection.commit()
        print("✅ Transaction committed")
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        if connection:
            connection.rollback()
            print("🔄 Transaction rolled back")
        raise
    
    finally:
        if cursor:
            cursor.close()
            print("🔒 Database cursor closed")

def test_connection() -> bool:
    """
    Test database connectivity
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_database_cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print("✅ Database connection test successful")
                return True
            else:
                print("❌ Database connection test failed - unexpected result")
                return False
                
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def execute_query(query: str, params: tuple = None, fetch: str = "all") -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as list of dictionaries
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Query parameters
        fetch (str): "all", "one", or "many" (default: "all")
        
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries
        
    Example:
        users = execute_query("SELECT * FROM Users WHERE Username = ?", ("john_doe",))
    """
    try:
        with get_database_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch results based on fetch parameter
            if fetch == "one":
                row = cursor.fetchone()
                if row:
                    return [dict(zip(columns, row))]
                return []
            elif fetch == "many":
                rows = cursor.fetchmany()
            else:  # fetch == "all"
                rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in rows]
            
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        raise

def execute_non_query(query: str, params: tuple = None) -> int:
    """
    Execute INSERT, UPDATE, or DELETE query
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Query parameters
        
    Returns:
        int: Number of affected rows
        
    Example:
        rows_affected = execute_non_query(
            "INSERT INTO Users (Username, Email, PasswordHash) VALUES (?, ?, ?)",
            ("john_doe", "john@example.com", "hashed_password")
        )
    """
    try:
        with get_database_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.rowcount
            
    except Exception as e:
        print(f"❌ Non-query execution failed: {e}")
        raise

def execute_scalar(query: str, params: tuple = None) -> Any:
    """
    Execute query and return single value (first column of first row)
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Query parameters
        
    Returns:
        Any: Single value result
        
    Example:
        user_count = execute_scalar("SELECT COUNT(*) FROM Users")
        user_id = execute_scalar("SELECT UserID FROM Users WHERE Username = ?", ("john_doe",))
    """
    try:
        with get_database_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            return result[0] if result else None
            
    except Exception as e:
        print(f"❌ Scalar query execution failed: {e}")
        raise

def get_database_stats() -> Dict[str, Any]:
    """
    Get basic database statistics for monitoring
    
    Returns:
        Dict[str, Any]: Database statistics
    """
    try:
        stats = {}
        
        # Get table row counts
        tables = ['Users', 'Recipes', 'Tags', 'Likes', 'Favorites', 'RecipeTags']
        for table in tables:
            try:
                count = execute_scalar(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table.lower()}_count"] = count
            except Exception as e:
                stats[f"{table.lower()}_count"] = f"Error: {e}"
        
        stats["connection_status"] = "healthy"
        stats["timestamp"] = time.time()
        
        return stats
        
    except Exception as e:
        return {
            "connection_status": f"unhealthy: {e}",
            "timestamp": time.time()
        }

def get_connection_info() -> Dict[str, str]:
    """
    Get database connection information for debugging
    
    Returns:
        Dict[str, str]: Connection information (without sensitive data)
    """
    return {
        "server": DATABASE_CONFIG["server"],
        "database": DATABASE_CONFIG["database"],
        "driver": DATABASE_CONFIG["driver"],
        "connection_string": CONNECTION_STRING.replace(DATABASE_CONFIG["password"], "***")
    }

# Dependency function for FastAPI
def get_db_cursor():
    """
    FastAPI dependency function to get database cursor
    
    This can be used with FastAPI's dependency injection:
    
    @app.get("/users/")
    async def get_users(cursor = Depends(get_db_cursor)):
        cursor.execute("SELECT * FROM Users")
        return cursor.fetchall()
    """
    with get_database_cursor() as cursor:
        yield cursor

# Utility functions for common operations
def insert_and_get_id(table: str, columns: List[str], values: tuple) -> int:
    """
    Insert a record and return the generated ID
    
    Args:
        table (str): Table name
        columns (List[str]): Column names
        values (tuple): Values to insert
        
    Returns:
        int: Generated ID
        
    Example:
        user_id = insert_and_get_id(
            "Users", 
            ["Username", "Email", "PasswordHash"],
            ("john_doe", "john@example.com", "hash")
        )
    """
    placeholders = ", ".join(["?" for _ in values])
    columns_str = ", ".join(columns)
    
    query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
    
    try:
        with get_database_cursor() as cursor:
            cursor.execute(query, values)
            cursor.execute("SELECT @@IDENTITY")
            return cursor.fetchone()[0]
    except Exception as e:
        print(f"❌ Insert operation failed: {e}")
        raise

def check_table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database
    
    Args:
        table_name (str): Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        query = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = ?
        """
        count = execute_scalar(query, (table_name,))
        return count > 0
    except Exception as e:
        print(f"❌ Error checking table existence: {e}")
        return False

# Initialize database verification
def verify_database_setup():
    """
    Verify that all required tables exist
    """
    required_tables = ['Users', 'Recipes', 'Tags', 'Likes', 'Favorites', 'RecipeTags']
    
    print("🔍 Verifying database setup...")
    
    for table in required_tables:
        if check_table_exists(table):
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' is missing!")
            raise Exception(f"Required table '{table}' not found in database")
    
    print("✅ All required tables verified")