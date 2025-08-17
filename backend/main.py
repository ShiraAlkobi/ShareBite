from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from database import test_connection, get_database_stats
# from routers import recipes, users, tags

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    - Startup: Test database connection
    - Shutdown: Clean up resources
    """
    print("🚀 Starting Recipe Sharing Platform Backend...")
    
    # Test database connection on startup
    try:
        if test_connection():
            print("✅ Database connection verified successfully")
        else:
            print("❌ Database connection failed")
            raise Exception("Cannot connect to database")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
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
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (Controllers in MVC pattern)
# app.include_router(
#     users.router,
#     prefix="/api/users",
#     tags=["Users"]
# )

# app.include_router(
#     recipes.router,
#     prefix="/api/recipes", 
#     tags=["Recipes"]
# )

# app.include_router(
#     tags.router,
#     prefix="/api/tags",
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
        "docs": "/docs"
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
            "database_stats": stats
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
    return HTTPException(
        status_code=500,
        detail="Internal server error occurred"
    )

if __name__ == "__main__":
    """
    Run the server directly for development
    Production deployment should use a proper ASGI server
    """
    print("🔧 Running in development mode...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )