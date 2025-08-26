import pyodbc
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from queue import Queue, Empty
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

# Global connection pool
_connection_pool = None
_pool_lock = threading.Lock()

class ConnectionPool:
    """
    Simple connection pool for database connections
    Reuses connections to avoid connection overhead
    """
    def __init__(self, connection_string: str, max_connections: int = 10):
        self.connection_string = connection_string
        self.pool = Queue(maxsize=max_connections)
        self.max_connections = max_connections
        self.active_connections = 0
        self.lock = threading.Lock()
        
        # Create initial connections
        print("Initializing connection pool...")
        for i in range(min(3, max_connections)):  # Start with 3 connections
            try:
                conn = pyodbc.connect(connection_string)
                self.pool.put(conn)
                self.active_connections += 1
                print(f"Created initial connection {i+1}/3")
            except Exception as e:
                print(f"Failed to create initial connection {i+1}: {e}")
                break
        
        print(f"Connection pool initialized with {self.active_connections} connections")
    
    def get_connection(self):
        """Get a connection from the pool or create new one if needed"""
        try:
            # Try to get existing connection (non-blocking)
            conn = self.pool.get_nowait()
            
            # Test if connection is still alive
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return conn
            except:
                # Connection is dead, don't return it
                with self.lock:
                    self.active_connections -= 1
                print("Removed dead connection from pool")
        except Empty:
            # No connections available in pool
            pass
        
        # Create new connection if under limit
        with self.lock:
            if self.active_connections < self.max_connections:
                try:
                    print(f"Creating new connection ({self.active_connections + 1}/{self.max_connections})")
                    conn = pyodbc.connect(self.connection_string)
                    self.active_connections += 1
                    return conn
                except Exception as e:
                    print(f"Failed to create connection: {e}")
                    raise
        
        # Wait for connection to become available
        try:
            print("Waiting for available connection...")
            return self.pool.get(timeout=30)
        except Empty:
            raise Exception("Timeout waiting for database connection")
    
    def return_connection(self, conn):
        """Return connection to pool or close if pool is full"""
        if not conn:
            return
            
        try:
            # Test connection before returning to pool
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            # Connection is good, try to return to pool
            self.pool.put_nowait(conn)
        except Empty:
            # Pool is full, close the connection
            try:
                conn.close()
                with self.lock:
                    self.active_connections -= 1
            except:
                pass
        except:
            # Connection is bad, close it
            try:
                conn.close()
                with self.lock:
                    self.active_connections -= 1
            except:
                pass
    
    def close_all(self):
        """Close all connections in pool"""
        print("Closing all pooled connections...")
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass
        with self.lock:
            self.active_connections = 0

def get_connection():
    """
    Get a database connection from the pool
    
    Returns:
        pyodbc.Connection: Database connection
    """
    global _connection_pool
    
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool(CONNECTION_STRING)
    
    return _connection_pool.get_connection()

def return_connection(conn):
    """
    Return a database connection to the pool
    """
    global _connection_pool
    if _connection_pool and conn:
        _connection_pool.return_connection(conn)

def close_connection():
    """
    This function is kept for backward compatibility but doesn't do much now
    since connections are managed by the pool
    """
    pass

@contextmanager
def get_database_cursor():
    """
    Context manager for database operations with connection pooling
    
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
        
        yield cursor
        
        # Commit the transaction if no errors occurred
        connection.commit()
        
    except Exception as e:
        print(f"Database operation failed: {e}")
        if connection:
            try:
                connection.rollback()
                print("Transaction rolled back")
            except:
                pass
        raise
    
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            return_connection(connection)  # Return to pool instead of closing

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
                print("Database connection test successful")
                return True
            else:
                print("Database connection test failed - unexpected result")
                return False
                
    except Exception as e:
        print(f"Database connection test failed: {e}")
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
        print(f"Query execution failed: {e}")
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
        print(f"Non-query execution failed: {e}")
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
        print(f"Scalar query execution failed: {e}")
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
        
        # Add pool statistics
        global _connection_pool
        if _connection_pool:
            stats["pool_active_connections"] = _connection_pool.active_connections
            stats["pool_available_connections"] = _connection_pool.pool.qsize()
            stats["pool_max_connections"] = _connection_pool.max_connections
        
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
    info = {
        "server": DATABASE_CONFIG["server"],
        "database": DATABASE_CONFIG["database"],
        "driver": DATABASE_CONFIG["driver"],
        "connection_string": CONNECTION_STRING.replace(DATABASE_CONFIG["password"], "***")
    }
    
    # Add pool info if available
    global _connection_pool
    if _connection_pool:
        info["pool_active"] = str(_connection_pool.active_connections)
        info["pool_available"] = str(_connection_pool.pool.qsize())
        info["pool_max"] = str(_connection_pool.max_connections)
    
    return info

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
        print(f"Insert operation failed: {e}")
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
        print(f"Error checking table existence: {e}")
        return False

# Initialize database verification
def verify_database_setup():
    """
    Verify that all required tables exist
    """
    required_tables = ['Users', 'Recipes', 'Tags', 'Likes', 'Favorites', 'RecipeTags']
    
    print("Verifying database setup...")
    
    for table in required_tables:
        if check_table_exists(table):
            print(f"Table '{table}' exists")
        else:
            print(f"Table '{table}' is missing!")
            raise Exception(f"Required table '{table}' not found in database")
    
    print("All required tables verified")

# Cleanup function for graceful shutdown
def cleanup_connections():
    """
    Close all pooled connections - call this during application shutdown
    """
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None
        print("Database connection pool cleaned up")