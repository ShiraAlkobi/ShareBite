# gateway.py - API Gateway for ShareBite
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import time
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
from collections import defaultdict
import asyncio

app = FastAPI(
    title="ShareBite API Gateway",
    description="API Gateway for ShareBite Recipe Sharing Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service registry - your current backend runs on port 8000
SERVICES = {
    "backend": os.getenv("BACKEND_URL", "http://localhost:8001"),  # Your existing FastAPI app will move here
    "ollama": os.getenv("OLLAMA_URL", "http://localhost:11434")
}

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)
ai_request_counts = defaultdict(list)

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, client_id: str, request_type: str = "general") -> bool:
        now = time.time()
        
        # Choose the appropriate storage
        if request_type == "ai":
            storage = ai_request_counts
            # More restrictive for AI endpoints
            max_reqs = 10  # 10 AI requests per minute
        else:
            storage = request_counts
            max_reqs = self.max_requests
        
        # Clean old requests
        storage[client_id] = [
            req_time for req_time in storage[client_id] 
            if now - req_time < self.window_seconds
        ]
        
        if len(storage[client_id]) >= max_reqs:
            return False
        
        storage[client_id].append(now)
        return True

rate_limiter = RateLimiter()

# Request logging
class RequestLogger:
    @staticmethod
    def log_request(request: Request, response_status: int, duration: float):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{request.client.host} - {request.method} {request.url.path} - "
              f"Status: {response_status} - Duration: {duration:.2f}s")

logger = RequestLogger()

@app.middleware("http")
async def rate_limit_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Rate limiting
    client_ip = request.client.host
    request_type = "ai" if "/chat/" in str(request.url) else "general"
    
    if not rate_limiter.is_allowed(client_ip, request_type):
        duration = time.time() - start_time
        logger.log_request(request, 429, duration)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    # Process request
    response = await call_next(request)
    
    # Log request
    duration = time.time() - start_time
    logger.log_request(request, response.status_code, duration)
    
    return response

@app.get("/health")
async def gateway_health():
    """Gateway health check"""
    return {
        "gateway_status": "healthy",
        "timestamp": time.time(),
        "services": {
            "backend": await check_service_health("backend"),
            "ollama": await check_service_health("ollama")
        }
    }

async def check_service_health(service_name: str) -> str:
    """Check if a service is healthy"""
    try:
        if service_name not in SERVICES:
            return "not_configured"
        
        async with httpx.AsyncClient() as client:
            if service_name == "ollama":
                response = await client.get(f"{SERVICES[service_name]}/api/tags", timeout=3)
            else:
                response = await client.get(f"{SERVICES[service_name]}/health", timeout=3)
            
            return "healthy" if response.status_code == 200 else "unhealthy"
    except:
        return "unreachable"

# Authentication middleware
async def extract_user_from_token(request: Request) -> Optional[str]:
    """Extract user info from JWT token for logging purposes"""
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # In a real implementation, you'd decode the JWT
            # For now, just return a placeholder
            return token[:10] + "..."
        return None
    except:
        return None

# Main proxy route - handles all API requests
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(path: str, request: Request):
    """
    Proxy all /api/v1/* requests to your existing backend
    This preserves all your existing route logic
    """
    try:
        # Forward to your existing FastAPI backend
        target_url = f"{SERVICES['backend']}/api/v1/{path}"
        
        # Extract request data
        headers = dict(request.headers)
        
        # Remove hop-by-hop headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Get request body
        body = await request.body()
        
        # Add gateway headers
        headers["X-Gateway"] = "ShareBite-Gateway"
        user_info = await extract_user_from_token(request)
        if user_info:
            headers["X-User-Token"] = user_info
        
        async with httpx.AsyncClient() as client:
            # Forward the request to backend
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=120.0  # Longer timeout for AI endpoints
            )
            
            # Return the response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail="Backend service unavailable"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Backend service timeout"
        )
    except Exception as e:
        print(f"Gateway error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Gateway internal error"
        )

# Optional: Direct Ollama proxy for debugging (you might not need this)
@app.api_route("/ollama/{path:path}", methods=["GET", "POST"])
async def proxy_to_ollama(path: str, request: Request):
    """
    Optional direct proxy to Ollama for debugging
    Your backend should still use Ollama directly
    """
    try:
        target_url = f"{SERVICES['ollama']}/{path}"
        
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        body = await request.body()
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=120.0
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    
    except Exception as e:
        print(f"Ollama proxy error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Ollama service unavailable"
        )

# Gateway statistics endpoint
@app.get("/gateway/stats")
async def gateway_stats():
    """Get gateway statistics"""
    now = time.time()
    
    # Clean old entries
    active_clients = 0
    active_ai_clients = 0
    
    for client_id, requests in request_counts.items():
        recent_requests = [r for r in requests if now - r < 300]  # Last 5 minutes
        if recent_requests:
            active_clients += 1
    
    for client_id, requests in ai_request_counts.items():
        recent_requests = [r for r in requests if now - r < 300]  # Last 5 minutes
        if recent_requests:
            active_ai_clients += 1
    
    return {
        "active_clients_5min": active_clients,
        "active_ai_clients_5min": active_ai_clients,
        "total_tracked_clients": len(request_counts),
        "total_ai_clients": len(ai_request_counts),
        "uptime": "N/A",  # Implement if needed
        "services": SERVICES
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)