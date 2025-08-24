from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Any
from datetime import datetime

class ChatModel(QObject):
    """
    Chat data model - handles AI chat history and state
    Part of MVP pattern - Model layer
    """
    
    # Signals for UI updates
    message_added = Signal(dict)
    chat_cleared = Signal()
    
    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.current_context = {}
        
    def add_message(self, message: Dict[str, Any]):
        """Add message to chat history"""
        # Ensure message has required fields
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
            
        self.chat_history.append(message)
        self.message_added.emit(message)
        
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get full chat history"""
        return self.chat_history
        
    def set_chat_history(self, history: List[Dict[str, Any]]):
        """Set chat history from API"""
        self.chat_history = history
        
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history = []
        self.current_context = {}
        self.chat_cleared.emit()
        
    def set_context(self, context: Dict[str, Any]):
        """Set current chat context"""
        self.current_context = context
        
    def get_context(self) -> Dict[str, Any]:
        """Get current chat context"""
        return self.current_context
        
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages for context"""
        return self.chat_history[-count:] if len(self.chat_history) > count else self.chat_history