from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from auth_routes import verify_token
from services.rag_chat_service import RAGChatService
import requests
import json

router = APIRouter(prefix="/chat", tags=["AI Chat"])

# Initialize RAG service
rag_service = RAGChatService()

# Pydantic models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    relevant_recipes_count: int
    recipe_ids: List[int]
    search_intent: str
    success: bool

class ConversationHistoryResponse(BaseModel):
    history: List[Dict[str, Any]]

# @router.post("", response_model=ChatResponse)
# async def chat_with_ai(
#     chat_message: ChatMessage,
#     current_user: dict = Depends(verify_token)
# ):
#     """
#     Chat with AI using RAG - searches recipes and generates AI response
#     """
#     try:
#         user_id = current_user['userid']
#         username = current_user['username']
        
#         print(f"Chat request from {username} (ID: {user_id}): {chat_message.message}")
        
#         # Validate message
#         if not chat_message.message or not chat_message.message.strip():
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Message cannot be empty"
#             )
        
#         # Process chat message using RAG
#         result = rag_service.process_chat_message(user_id, chat_message.message.strip())
        
#         if not result["success"]:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=result.get("error", "Failed to process chat message")
#             )
        
#         return ChatResponse(
#             response=result["response"],
#             relevant_recipes_count=result["relevant_recipes_count"],
#             recipe_ids=result["recipe_ids"],
#             search_intent=result["search_intent"],
#             success=True
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in chat endpoint: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error occurred"
#         )

@router.get("/history", response_model=ConversationHistoryResponse)
async def get_chat_history(
    limit: int = 5,
    current_user: dict = Depends(verify_token)
):
    """
    Get conversation history for current user
    """
    try:
        user_id = current_user['userid']
        
        history = rag_service.get_conversation_history(user_id, limit)
        
        return ConversationHistoryResponse(history=history)
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation history"
        )

@router.delete("/history")
async def clear_chat_history(current_user: dict = Depends(verify_token)):
    """
    Clear conversation history for current user
    """
    try:
        user_id = current_user['userid']
        
        rag_service.clear_conversation_history(user_id)
        
        return {"message": "Conversation history cleared successfully"}
        
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation history"
        )

@router.get("/status")
async def get_chat_service_status():
    """
    Check if AI chat service is available
    """
    try:
        # Test Ollama connection
        ollama_available = rag_service.ollama_client.test_connection()
        
        return {
            "ollama_available": ollama_available,
            "service_status": "healthy" if ollama_available else "degraded",
            "message": "AI chat service is ready" if ollama_available else "AI service temporarily unavailable"
        }
        
    except Exception as e:
        print(f"Error checking chat service status: {e}")
        return {
            "ollama_available": False,
            "service_status": "unhealthy",
            "message": f"Service error: {str(e)}"
        }
    


# Add this to your existing router
class RecipeContextChatRequest(BaseModel):
    message: str
    recipe_context: Dict[str, Any]

class SimpleChatResponse(BaseModel):
    response: str

@router.post("/recipe-chat", response_model=SimpleChatResponse)
async def recipe_context_chat(
    chat_request: RecipeContextChatRequest,
    current_user: dict = Depends(verify_token)
):
    try:
        # Validate and truncate message
        message = chat_request.message.strip()[:200]  # Limit user message length
        
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Create ultra-focused prompt
        prompt = create_optimized_recipe_prompt(message, chat_request.recipe_context)
        
        ollama_payload = {
            "model": "mistral:7b-instruct-q4_0",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.7,
                "num_predict": 80,      # Even shorter responses
                "num_ctx": 512,         # Smaller context
                "repeat_penalty": 1.1,
                "stop": ["\n\n", "User:", "###"]
            },
            "keep_alive": "15m"  # Keep model loaded
        }
        
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json=ollama_payload,
            timeout=120  # REDUCED timeout
        )
        
        if ollama_response.status_code == 200:
            ai_data = ollama_response.json()
            ai_response = ai_data.get("response", "Try rephrasing your question.").strip()
            return SimpleChatResponse(response=ai_response)
        else:
            return SimpleChatResponse(response="AI is busy, please try again.")
            
    except requests.exceptions.Timeout:
        return SimpleChatResponse(response="Response timed out. Try a shorter question.")
    except Exception as e:
        return SimpleChatResponse(response="Chat temporarily unavailable.")

def create_optimized_recipe_prompt(message: str, recipe: Dict) -> str:
    """Ultra-concise prompt for speed"""
    title = recipe.get('title', 'Recipe')[:30]
    ingredients = recipe.get('ingredients', '')[:100]
    
    return f"Recipe: {title}\nIngredients: {ingredients}\nQ: {message}\nA:"

# def create_recipe_focused_prompt(user_message: str, recipe_context: Dict[str, Any]) -> str:
#     """Create a very concise prompt for fast responses"""
    
#     # Extract only essential recipe data
#     title = recipe_context.get('title', 'Unknown Recipe')
#     ingredients = recipe_context.get('ingredients', 'No ingredients')[:200]  # Limit length
#     instructions = recipe_context.get('instructions', 'No instructions')[:300]  # Limit length
    
#     # Create ultra-concise prompt for speed
#     prompt = f"""Recipe: {title}

# Ingredients: {ingredients}

# Instructions: {instructions}

# Question: {user_message}

# Answer briefly and directly:"""
    
#     return prompt