import requests
import json
from typing import Dict, Any, Optional, List

class OllamaClient:
    """
    Optimized Ollama client for fast responses
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "mistral:7b-instruct-q4_0"
        
    def test_connection(self) -> bool:
        """Test Ollama availability"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        Generate fast response with optimized settings
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,      # Lower = more focused, faster
                    "top_p": 0.8,            # Reduced for speed
                    "num_predict": 300,      # Limit response length (was max_tokens)
                    "num_ctx": 2048,         # Smaller context window
                    "repeat_penalty": 1.1,   # Prevent repetition
                    "stop": ["\n\n\n", "User:", "Human:"]  # Stop sequences
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            print(f"Sending to Ollama (length: {len(prompt)} chars)")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Reduced from 600 seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                print(f"Generated response: {len(ai_response)} chars")
                return ai_response
            else:
                print(f"Ollama error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("Ollama timeout after 30 seconds")
            return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None