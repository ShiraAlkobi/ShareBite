# start_backend.py - Starts your existing ShareBite backend server
import subprocess
import sys
import os

def start_sharebite_backend():
    """Start the ShareBite backend server on port 8001"""
    print("🚀 Starting ShareBite Backend Server...")
    print("📍 Server will run on: http://127.0.0.1:8001")
    print("📚 API Documentation: http://127.0.0.1:8001/docs")
    print("💗 Health Check: http://127.0.0.1:8001/health")
    print("")
    
    try:
        # Run your existing main.py (make sure it's configured for port 8001)
        subprocess.run([
            sys.executable, "main.py"
        ], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

if __name__ == "__main__":
    start_sharebite_backend()
