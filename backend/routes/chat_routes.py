from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from auth_routes import verify_token
from services.rag_chat_service import RAGChatService

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

@router.post("", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    current_user: dict = Depends(verify_token)
):
    """
    Chat with AI using RAG - searches recipes and generates AI response
    """
    try:
        user_id = current_user['userid']
        username = current_user['username']
        
        print(f"Chat request from {username} (ID: {user_id}): {chat_message.message}")
        
        # Validate message
        if not chat_message.message or not chat_message.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Process chat message using RAG
        result = rag_service.process_chat_message(user_id, chat_message.message.strip())
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to process chat message")
            )
        
        return ChatResponse(
            response=result["response"],
            relevant_recipes_count=result["relevant_recipes_count"],
            recipe_ids=result["recipe_ids"],
            search_intent=result["search_intent"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

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