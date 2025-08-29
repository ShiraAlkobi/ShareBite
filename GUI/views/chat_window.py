"""
AI Chat Window - RAG-powered Recipe Assistant
Implements MVP pattern - View layer for AI chat interface
Includes chat history, context management, and RAG features
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QFrame, QTextEdit, QProgressBar,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QTextCursor, QPixmap
from services.api_service import APIManager
from models.chat_model import ChatModel
from typing import Dict, List, Any, Optional
import json
import re


class ChatBubble(QFrame):
    """Individual chat message bubble"""
    
    def __init__(self, message: Dict[str, Any], is_user: bool = True):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.setup_ui()
        
    def setup_ui(self):
        """Setup chat bubble UI"""
        self.setObjectName("userBubble" if self.is_user else "aiBubble")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)
        
        # Message content
        content = self.message.get('content', '')
        message_label = QLabel(content)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # Timestamp
        timestamp = self.message.get('timestamp', '')
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setObjectName("timeLabel")
            time_label.setAlignment(Qt.AlignRight if self.is_user else Qt.AlignLeft)
            layout.addWidget(time_label)
            
        # Apply styling based on sender
        self.setStyleSheet(self.get_bubble_styles())
        
    def get_bubble_styles(self) -> str:
        """Get bubble-specific styles"""
        if self.is_user:
            return """
                QFrame#userBubble {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    border-radius: 12px;
                    margin: 5px 50px 5px 5px;
                }
                QLabel#messageText {
                    color: white;
                    font-size: 11pt;
                }
                QLabel#timeLabel {
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 8pt;
                }
            """
        else:
            return """
                QFrame#aiBubble {
                    background-color: #f1f3f4;
                    border: 1px solid #e1e8ed;
                    border-radius: 12px;
                    margin: 5px 5px 5px 50px;
                }
                QLabel#messageText {
                    color: #2c3e50;
                    font-size: 11pt;
                    line-height: 1.4;
                }
                QLabel#timeLabel {
                    color: #6c757d;
                    font-size: 8pt;
                }
            """


class ChatWindow(QWidget):
    """
    AI Chat window with RAG capabilities
    Provides recipe assistance, cooking tips, and general food-related queries
    """
    
    # Signals
    back_to_home = Signal()
    
    def __init__(self, api_service, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.api_manager = APIManager(api_service)
        self.chat_model = ChatModel()
        
        self.is_typing = False
        self.current_context = {}
        
        self.setup_ui()
        self.setup_connections()
        self.load_chat_history()
        
    def setup_ui(self):
        """Setup chat window UI"""
        self.setObjectName("ChatWindow")
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Left sidebar with context and suggestions
        self.setup_sidebar(main_layout)
        
        # Main chat area
        self.setup_chat_area(main_layout)
        
        # Apply styling
        self.setStyleSheet(self.get_chat_styles())
        
    def setup_sidebar(self, main_layout):
        """Setup left sidebar with context and suggestions"""
        sidebar = QFrame()
        sidebar.setObjectName("chatSidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Context section
        context_group = QFrame()
        context_group.setObjectName("contextGroup")
        context_layout = QVBoxLayout(context_group)
        
        context_title = QLabel("הקשר שיחה")
        context_title.setObjectName("sidebarTitle")
        context_layout.addWidget(context_title)
        
        # Context type selector
        self.context_selector = QComboBox()
        self.context_selector.setObjectName("contextSelector")
        self.context_selector.addItems([
            "שיחה כללית",
            "עזרה במתכון ספציפי",
            "המלצות למתכונים",
            "שאלות תזונה",
            "טכניקות בישול"
        ])
        context_layout.addWidget(self.context_selector)
        
        # Current recipe context (if any)
        self.context_recipe_label = QLabel("אין מתכון נבחר")
        self.context_recipe_label.setObjectName("contextLabel")
        self.context_recipe_label.setWordWrap(True)
        context_layout.addWidget(self.context_recipe_label)
        
        sidebar_layout.addWidget(context_group)
        
        # Quick suggestions
        suggestions_group = QFrame()
        suggestions_group.setObjectName("suggestionsGroup")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        suggestions_title = QLabel("הצעות מהירות")
        suggestions_title.setObjectName("sidebarTitle")
        suggestions_layout.addWidget(suggestions_title)
        
        # Suggestion buttons
        suggestions = [
            "איך להכין פסטה מושלמת?",
            "תחליפים טבעוניים לביצים",
            "איך לשמור על ירקות טריים?",
            "טיפים לבישול אורז",
            "איך להכין רוטב עגבניות?"
        ]
        
        for suggestion in suggestions:
            btn = QPushButton(suggestion)
            btn.setObjectName("suggestionButton")
            btn.clicked.connect(lambda checked, text=suggestion: self.send_suggestion(text))
            suggestions_layout.addWidget(btn)
            
        sidebar_layout.addWidget(suggestions_group)
        
        # Chat actions
        actions_group = QFrame()
        actions_group.setObjectName("actionsGroup")
        actions_layout = QVBoxLayout(actions_group)
        
        actions_title = QLabel("פעולות")
        actions_title.setObjectName("sidebarTitle")
        actions_layout.addWidget(actions_title)
        
        self.clear_chat_button = QPushButton("נקה שיחה")
        self.clear_chat_button.setObjectName("actionButton")
        actions_layout.addWidget(self.clear_chat_button)
        
        self.export_chat_button = QPushButton("ייצא שיחה")
        self.export_chat_button.setObjectName("actionButton")
        actions_layout.addWidget(self.export_chat_button)
        
        sidebar_layout.addWidget(actions_group)
        sidebar_layout.addStretch()
        
        main_layout.addWidget(sidebar)
        
    def setup_chat_area(self, main_layout):
        """Setup main chat area"""
        chat_container = QFrame()
        chat_container.setObjectName("chatContainer")
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(10)
        
        # Header
        self.setup_chat_header(chat_layout)
        
        # Chat messages area
        self.setup_messages_area(chat_layout)
        
        # Input area
        self.setup_input_area(chat_layout)
        
        main_layout.addWidget(chat_container)
        
    def setup_chat_header(self, chat_layout):
        """Setup chat header"""
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← חזור לעמוד הבית")
        self.back_button.setObjectName("backButton")
        header_layout.addWidget(self.back_button)
        
        # Title
        chat_title = QLabel("🤖 עוזר הבישול החכם")
        chat_title.setObjectName("chatTitle")
        header_layout.addWidget(chat_title)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("מוכן לעזור")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)
        
        chat_layout.addLayout(header_layout)
        
    def setup_messages_area(self, chat_layout):
        """Setup messages display area"""
        # Scroll area for messages
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setObjectName("messagesScroll")
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Messages container
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()  # Push messages to bottom
        
        self.messages_scroll.setWidget(self.messages_container)
        chat_layout.addWidget(self.messages_scroll)
        
        # Typing indicator
        self.typing_indicator = QLabel("🤖 הבוט כותב...")
        self.typing_indicator.setObjectName("typingIndicator")
        self.typing_indicator.setVisible(False)
        chat_layout.addWidget(self.typing_indicator)
        
    def setup_input_area(self, chat_layout):
        """Setup message input area"""
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(input_frame)
        
        # Main input area
        main_input_layout = QHBoxLayout()
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("כתבו את השאלה שלכם כאן...")
        self.message_input.setMaximumHeight(100)
        main_input_layout.addWidget(self.message_input)
        
        # Send button
        self.send_button = QPushButton("שלח")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(60, 60)
        main_input_layout.addWidget(self.send_button)
        
        input_layout.addLayout(main_input_layout)
        
        # Quick actions
        quick_actions_layout = QHBoxLayout()
        
        self.voice_button = QPushButton("🎤")
        self.voice_button.setObjectName("quickButton")
        self.voice_button.setToolTip("הקלטה קולית (בקרוב)")
        quick_actions_layout.addWidget(self.voice_button)
        
        self.recipe_suggest_button = QPushButton("💡")
        self.recipe_suggest_button.setObjectName("quickButton")
        self.recipe_suggest_button.setToolTip("המלצות למתכונים")
        quick_actions_layout.addWidget(self.recipe_suggest_button)
        
        self.nutrition_button = QPushButton("🥗")
        self.nutrition_button.setObjectName("quickButton")
        self.nutrition_button.setToolTip("שאלות תזונה")
        quick_actions_layout.addWidget(self.nutrition_button)
        
        quick_actions_layout.addStretch()
        
        # Character count
        self.char_count_label = QLabel("0/500")
        self.char_count_label.setObjectName("charCountLabel")
        quick_actions_layout.addWidget(self.char_count_label)
        
        input_layout.addLayout(quick_actions_layout)
        
        chat_layout.addWidget(input_frame)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Navigation
        self.back_button.clicked.connect(self.back_to_home.emit)
        
        # Chat actions
        self.send_button.clicked.connect(self.send_message)
        self.clear_chat_button.clicked.connect(self.clear_chat)
        self.export_chat_button.clicked.connect(self.export_chat)
        
        # Quick actions
        self.voice_button.clicked.connect(self.handle_voice_input)
        self.recipe_suggest_button.clicked.connect(self.request_recipe_suggestions)
        self.nutrition_button.clicked.connect(self.ask_nutrition_question)
        
        # Input events
        self.message_input.textChanged.connect(self.on_text_changed)
        
        # Context selector
        self.context_selector.currentTextChanged.connect(self.on_context_changed)
        
        # Model signals
        self.chat_model.message_added.connect(self.on_message_added)
        self.chat_model.chat_cleared.connect(self.on_chat_cleared)
        
        # Enter key handling
        self.message_input.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """Handle keyboard events"""
        if obj == self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
        
    def send_message(self):
        """Send user message"""
        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return
            
        # Create user message
        user_message = {
            'content': message_text,
            'sender': 'user',
            'timestamp': QDateTime.currentDateTime().toString("hh:mm")
        }
        
        # Add to chat model
        self.chat_model.add_message(user_message)
        
        # Clear input
        self.message_input.clear()
        
        # Show typing indicator
        self.set_typing_indicator(True)
        
        # Prepare context for AI
        context = self.prepare_chat_context()
        
        # Send to AI
        self.api_manager.call_api(
            'chat_with_ai',
            success_callback=self.on_ai_response,
            error_callback=self.on_ai_error,
            message=message_text,
            context=context
        )
        
    def send_suggestion(self, suggestion_text: str):
        """Send a predefined suggestion"""
        self.message_input.setPlainText(suggestion_text)
        self.send_message()
        
    def prepare_chat_context(self) -> Dict[str, Any]:
        """Prepare context for AI chat"""
        context = {
            'chat_type': self.context_selector.currentText(),
            'recent_messages': self.chat_model.get_recent_messages(5),
            'user_preferences': {},  # Could include dietary restrictions, etc.
        }
        
        # Add recipe context if available
        if hasattr(self, 'current_recipe_context'):
            context['current_recipe'] = self.current_recipe_context
            
        return context
        
    def on_ai_response(self, result: Dict[str, Any]):
        """Handle AI response"""
        self.set_typing_indicator(False)
        
        ai_content = result.get('response', 'מצטער, לא הצלחתי להבין את השאלה.')
        
        # Create AI message
        ai_message = {
            'content': ai_content,
            'sender': 'ai',
            'timestamp': QDateTime.currentDateTime().toString("hh:mm"),
            'context': result.get('context', {})
        }
        
        # Add to chat model
        self.chat_model.add_message(ai_message)
        
    def on_ai_error(self, error: str):
        """Handle AI error"""
        self.set_typing_indicator(False)
        
        error_message = {
            'content': f"מצטער, אירעה שגיאה: {error}",
            'sender': 'ai',
            'timestamp': QDateTime.currentDateTime().toString("hh:mm"),
            'is_error': True
        }
        
        self.chat_model.add_message(error_message)
        
    def on_message_added(self, message: Dict[str, Any]):
        """Handle new message added to chat"""
        # Create and add chat bubble
        is_user = message.get('sender') == 'user'
        bubble = ChatBubble(message, is_user)
        
        # Insert before the stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_chat(self):
        """Clear chat history"""
        reply = QMessageBox.question(
            self,
            "נקה שיחה",
            "האם אתם בטוחים שברצונכם לנקות את השיחה?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chat_model.clear_chat()
            
    def on_chat_cleared(self):
        """Handle chat cleared"""
        # Remove all message widgets
        while self.messages_layout.count() > 1:  # Keep the stretch
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def export_chat(self):
        """Export chat history"""
        if not self.chat_model.get_chat_history():
            QMessageBox.information(self, "ייצוא צ'אט", "אין היסטוריית צ'אט לייצוא")
            return
            
        # Create export text
        export_text = "היסטוריית צ'אט - עוזר הבישול החכם\n"
        export_text += "=" * 50 + "\n\n"
        
        for message in self.chat_model.get_chat_history():
            sender = "אתה" if message.get('sender') == 'user' else "עוזר AI"
            timestamp = message.get('timestamp', '')
            content = message.get('content', '')
            
            export_text += f"[{timestamp}] {sender}:\n{content}\n\n"
            
        # Save to file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ייצא היסטוריית צ'אט",
            "chat_history.txt",
            "קבצי טקסט (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_text)
                QMessageBox.information(self, "הצלחה", f"היסטוריית הצ'אט נשמרה ב: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "שגיאה", f"שגיאה בשמירת הקובץ: {e}")
                
    def load_chat_history(self):
        """Load chat history from server"""
        # For now, we'll start with an empty chat
        # In a real implementation, you'd load from the API
        welcome_message = {
            'content': 'שלום! אני עוזר הבישול החכם שלכם. אני כאן לעזור עם מתכונים, טכניקות בישול, שאלות תזונה ועוד. איך אוכל לעזור לכם היום?',
            'sender': 'ai',
            'timestamp': QDateTime.currentDateTime().toString("hh:mm")
        }
        self.chat_model.add_message(welcome_message)
        
    def handle_voice_input(self):
        """Handle voice input (placeholder)"""
        QMessageBox.information(
            self,
            "הקלטה קולית",
            "פיצ'ר ההקלטה הקולית יהיה זמין בקרוב!"
        )
        
    def request_recipe_suggestions(self):
        """Request recipe suggestions from AI"""
        suggestion_text = "אני מחפש רעיונות למתכונים חדשים. תוכל להמליץ לי על כמה מתכונים מעניינים?"
        self.message_input.setPlainText(suggestion_text)
        self.send_message()
        
    def ask_nutrition_question(self):
        """Ask a nutrition-related question"""
        nutrition_text = "יש לי שאלה תזונתית - איך אוכל לוודא שאני מקבל מספיק חלבון ממקורות צמחיים?"
        self.message_input.setPlainText(nutrition_text)
        self.send_message()
        
    def on_text_changed(self):
        """Handle text input changes"""
        text = self.message_input.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"{char_count}/500")
        
        # Enable/disable send button
        self.send_button.setEnabled(bool(text.strip()) and char_count <= 500)
        
        # Change color if approaching limit
        if char_count > 450:
            self.char_count_label.setStyleSheet("color: #dc3545;")
        elif char_count > 400:
            self.char_count_label.setStyleSheet("color: #ffc107;")
        else:
            self.char_count_label.setStyleSheet("color: #6c757d;")
            
    def on_context_changed(self, context_type: str):
        """Handle context type change"""
        context_messages = {
            "שיחה כללית": "אני כאן לעזור עם כל שאלה הקשורה לבישול ואוכל!",
            "עזרה במתכון ספציפי": "בחרו מתכון ואני אעזור לכם איתו!",
            "המלצות למתכונים": "אשמח להמליץ על מתכונים בהתאם להעדפות שלכם!",
            "שאלות תזונה": "אני כאן לענות על שאלות תזונתיות ובריאותיות!",
            "טכניקות בישול": "בואו נלמד טכניקות בישול חדשות יחד!"
        }
        
        if context_type in context_messages:
            self.status_label.setText(context_messages[context_type])
            
    def set_recipe_context(self, recipe_data: Dict[str, Any]):
        """Set current recipe context for AI chat"""
        self.current_recipe_context = recipe_data
        recipe_title = recipe_data.get('title', 'מתכון לא ידוע')
        self.context_recipe_label.setText(f"מתכון נוכחי: {recipe_title}")
        
        # Switch to recipe-specific context
        self.context_selector.setCurrentText("עזרה במתכון ספציפי")
        
    def clear_recipe_context(self):
        """Clear recipe context"""
        if hasattr(self, 'current_recipe_context'):
            delattr(self, 'current_recipe_context')
        self.context_recipe_label.setText("אין מתכון נבחר")
        
    def set_typing_indicator(self, visible: bool):
        """Show/hide typing indicator"""
        self.typing_indicator.setVisible(visible)
        if visible:
            self.status_label.setText("הבוט כותב...")
            self.send_button.setEnabled(False)
        else:
            self.status_label.setText("מוכן לעזור")
            # Re-enable send button based on text content
            self.on_text_changed()
            
    def get_chat_styles(self) -> str:
        """Get chat window styles"""
        return """
            QWidget#ChatWindow {
                background-color: #f8f9fa;
            }
            
            QFrame#chatSidebar {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                margin-right: 10px;
            }
            
            QFrame#contextGroup, QFrame#suggestionsGroup, QFrame#actionsGroup {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin: 5px;
                padding: 10px;
            }
            
            QLabel#sidebarTitle {
                font-size: 11pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
            }
            
            QComboBox#contextSelector {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }
            
            QLabel#contextLabel {
                font-size: 9pt;
                color: #6c757d;
                margin-top: 5px;
                padding: 5px;
                background-color: white;
                border-radius: 4px;
            }
            
            QPushButton#suggestionButton {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                color: #1976d2;
                padding: 6px 10px;
                text-align: left;
                font-size: 9pt;
                margin: 2px 0;
            }
            
            QPushButton#suggestionButton:hover {
                background-color: #bbdefb;
                border-color: #64b5f6;
            }
            
            QPushButton#actionButton {
                background-color: #6c757d;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 6px 12px;
                font-size: 9pt;
                margin: 2px 0;
            }
            
            QPushButton#actionButton:hover {
                background-color: #5a6268;
            }
            
            QFrame#chatContainer {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
            }
            
            QPushButton#backButton {
                background-color: #6c757d;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 16px;
            }
            
            QPushButton#backButton:hover {
                background-color: #5a6268;
            }
            
            QLabel#chatTitle {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
            
            QLabel#statusLabel {
                font-size: 10pt;
                color: #28a745;
                padding: 10px;
                font-style: italic;
            }
            
            QScrollArea#messagesScroll {
                background-color: #fafbfc;
                border: none;
                border-radius: 8px;
                margin: 10px;
            }
            
            QLabel#typingIndicator {
                font-size: 10pt;
                color: #6c757d;
                font-style: italic;
                padding: 5px 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
                margin: 5px 10px;
            }
            
            QFrame#inputFrame {
                background-color: white;
                border-top: 1px solid #e9ecef;
                padding: 15px;
            }
            
            QTextEdit#messageInput {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 11pt;
                color: #2c3e50;
            }
            
            QTextEdit#messageInput:focus {
                border-color: #3498db;
                background-color: white;
            }
            
            QPushButton#sendButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
                border-radius: 30px;
                color: white;
                font-size: 14pt;
                font-weight: bold;
            }
            
            QPushButton#sendButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
            
            QPushButton#sendButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21618c, stop:1 #1b4f72);
            }
            
            QPushButton#sendButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            QPushButton#quickButton {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 20px;
                font-size: 14pt;
                padding: 8px;
                min-width: 35px;
                max-width: 35px;
                min-height: 35px;
                max-height: 35px;
            }
            
            QPushButton#quickButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            
            QLabel#charCountLabel {
                font-size: 9pt;
                color: #6c757d;
                padding: 5px;
            }
        """