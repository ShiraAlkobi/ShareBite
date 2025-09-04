import uvicorn
import os
import sys

def start_gateway():
    """Start the ShareBite API Gateway"""
    print("Starting ShareBite API Gateway...")
    print("Gateway running on: http://127.0.0.1:8000")
    print("Gateway stats: http://127.0.0.1:8000/gateway/stats")
    print("Gateway health: http://127.0.0.1:8000/health")
    print("Proxying to backend: http://127.0.0.1:8001")
    print("")
    
    # Run without reload to avoid the warning
    uvicorn.run(
        "gateway:app",  # Import string format
        host="0.0.0.0", 
        port=8000, 
        reload=False,  # Disabled reload to fix warning
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    start_gateway()

