import requests
import json
from typing import Dict, Any, Optional, List

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):  # Change this
        self.base_url = base_url
        self.model_name = "mistral:7b-instruct-q4_0" 
        self._ensure_model_loaded()  # Add this line
    
    def _ensure_model_loaded(self):
        """Preload model to avoid cold starts"""
        try:
            # Send a small warm-up request
            payload = {
                "model": self.model_name,
                "prompt": "Hi",
                "stream": False,
                "options": {
                    "num_predict": 5,
                    "num_ctx": 256
                }
            }
            requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
            print("Ollama model preloaded")
        except Exception as e:
            print(f"Model preload warning: {e}")
    def test_connection(self) -> bool:
        """Test Ollama availability"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,      # Lower = faster, more focused
                    "top_p": 0.7,            # Reduced for speed
                    "num_predict": 100,      # REDUCED from 200
                    "num_ctx": 1024,         # REDUCED from 2048
                    "repeat_penalty": 1.1,
                    "stop": ["\n\n", "User:", "Human:", "Question:"]
                }
            }
            
            # Add keep_alive to prevent model unloading
            payload["keep_alive"] = "15m"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60  # REDUCED from 120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            return None
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return None