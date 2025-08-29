from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from database import test_connection, get_database_stats

# Import authentication and recipe routes
from routes.auth_routes import router as auth_router
from routes.recipe_routes import router as recipe_router

# Import other routers when you create them
# from routers import recipes, users, tags

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    - Startup: Test database  connection
    - Shutdown: Clean up resources
    """
    print("🚀 Starting Recipe Sharing Platform Backend...")
    
    # Test database connection on startup
    try:
        if test_connection():
            print("✅ Database connection verified successfully")
            stats = get_database_stats()
            print(f"📊 Database stats: {stats}")
        else:
            print("❌ Database connection failed")
            raise Exception("Cannot connect to database")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    print("🔐 Authentication system initialized")
    print("📋 API Documentation available at: http://127.0.0.1:8000/docs")
    
    yield  # Application runs here
    
    print("🔄 Shutting down backend server...")

# Initialize FastAPI application
app = FastAPI(
    title="Recipe Sharing Platform API",
    description="Backend API for a recipe sharing and uploading platform with AI chat features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*",
        "http://0.0.0.0:*",
        "*"  # In production, specify exact origins
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(
    auth_router,
    prefix="/api/v1",
    tags=["Authentication"]
)

# Include recipe router
app.include_router(
    recipe_router,
    prefix="/api/v1",
    tags=["Recipes"]
)

# Include other routers when you create them
# app.include_router(
#     users.router,
#     prefix="/api/v1/users",
#     tags=["Users"]
# )

# app.include_router(
#     recipes.router,
#     prefix="/api/v1/recipes", 
#     tags=["Recipes"]
# )

# app.include_router(
#     tags.router,
#     prefix="/api/v1/tags",
#     tags=["Tags"]
# )

# Root endpoint
@app.get("/")
async def root():
    """
    Health check endpoint
    Returns basic API information
    """
    return {
        "message": "Recipe Sharing Platform API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "recipes": "/api/v1/recipes",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Detailed health check for monitoring
    """
    try:
        # Test database connection
        db_status = test_connection()
        stats = get_database_stats()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "api": "running",
            "database_stats": stats,
            "services": {
                "authentication": "active",
                "recipes": "active",
                "database": "connected" if db_status else "disconnected"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# Authentication endpoints info (for documentation)
@app.get("/api/v1/auth/info")
async def auth_info():
    """
    Get information about available authentication endpoints
    """
    return {
        "endpoints": {
            "login": "POST /api/v1/auth/login",
            "register": "POST /api/v1/auth/register", 
            "current_user": "GET /api/v1/auth/me",
            "logout": "POST /api/v1/auth/logout"
        },
        "description": "JWT-based authentication system",
        "token_type": "Bearer"
    }

if __name__ == "__main__":
    """
    Run the server directly for development
    Production deployment should use a proper ASGI server
    """
    print("🔧 Running in development mode...")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("📋 Alternative Docs: http://127.0.0.1:8000/redoc")
    print("💗 Health Check: http://127.0.0.1:8000/health")
    print("🔐 Authentication: http://127.0.0.1:8000/api/v1/auth/")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

from routes.chat_routes import router as chat_router

app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["Chat"]
)