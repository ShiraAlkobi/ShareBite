# check_services.py - Fixed with longer timeouts and better error handling
import requests
import json
import time

def check_service(name, url, timeout=10):
    """Check if a service is running with longer timeout"""
    try:
        print(f"Checking {name}...", end=" ")
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"Running ({response.status_code})")
            return True
        else:
            print(f"Responding but error ({response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("Not running or unreachable")
        return False
    except requests.exceptions.Timeout:
        print("Timeout (service too slow or not responding)")
        return False
    except Exception as e:
        print(f"Error - {e}")
        return False

def wait_for_service(name, url, max_attempts=6, delay=5):
    """Wait for a service to become available"""
    print(f"Waiting for {name} to start...")
    for attempt in range(max_attempts):
        if check_service(name, url, timeout=3):
            return True
        if attempt < max_attempts - 1:
            print(f"Attempt {attempt + 1}/{max_attempts}, waiting {delay}s...")
            time.sleep(delay)
    return False

def main():
    """Check all ShareBite services"""
    print("ShareBite Services Health Check")
    print("="*40)
    
    # Check services with longer timeouts
    services = [
        ("Backend Server", "http://127.0.0.1:8001/health"),
        ("API Gateway", "http://127.0.0.1:8000/health"), 
        ("Ollama AI", "http://127.0.0.1:11434/api/tags"),
    ]
    
    all_running = True
    
    for name, url in services:
        is_running = check_service(name, url, timeout=10)  # 10 second timeout
        if not is_running:
            all_running = False
    
    # Special check for gateway stats (might take longer to be available)
    print("\nChecking additional endpoints:")
    gateway_stats_running = check_service("Gateway Stats", "http://127.0.0.1:8000/gateway/stats", timeout=5)
    
    print("="*40)
    if all_running:
        print("All core services are running!")
        print("Your PySide6 client can connect to: http://127.0.0.1:8000")
        if not gateway_stats_running:
            print("Note: Gateway stats endpoint may still be initializing")
    else:
        print("Some services are not running")
        print("Start missing services and run this check again")
        
    # Show what's actually running
    print("\nService Status Summary:")
    for name, url in services:
        check_service(name, url, timeout=3)

if __name__ == "__main__":
    main()
