from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QScrollArea, QLineEdit, QSplitter,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from typing import Optional, List, Dict, Any
import json
import html
import ast

class ChatWidget(QFrame):
    """AI Chat widget integrated into recipe details"""
    
    chat_message_sent = Signal(str)  # message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatWidget")
        self.chat_history = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup chat interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Chat header
        header = QFrame()
        header.setObjectName("ChatHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        chat_icon = QLabel("🤖")
        chat_icon.setObjectName("ChatIcon")
        
        chat_title = QLabel("Recipe Assistant")
        chat_title.setObjectName("ChatTitle")
        
        header_layout.addWidget(chat_icon)
        header_layout.addWidget(chat_title)
        header_layout.addStretch()
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("ChatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setMaximumHeight(300)
        self.chat_display.setPlaceholderText("Ask me anything about this recipe...")
        
        # Chat input area
        input_frame = QFrame()
        input_frame.setObjectName("ChatInputFrame")
        
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("Ask about ingredients, cooking tips, substitutions...")
        self.chat_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("ChatSendButton")
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(header)
        layout.addWidget(self.chat_display)
        layout.addWidget(input_frame)
    
    def send_message(self):
        """Send chat message"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Add user message to display
        self.add_message("You", message, is_user=True)
        
        # Clear input
        self.chat_input.clear()
        
        # Show typing indicator
        self.show_typing_indicator()
        
        # Emit signal for processing
        self.chat_message_sent.emit(message)
    
    def add_message(self, sender: str, message: str, is_user: bool = False):
        """Add message to chat display"""
        timestamp = QTimer()
        
        if is_user:
            formatted_message = f'<div style="text-align: right; margin: 8px 0;"><strong style="color: #667eea;">{sender}:</strong><br><span style="background: #667eea; color: white; padding: 8px 12px; border-radius: 12px; display: inline-block; margin-top: 4px;">{message}</span></div>'
        else:
            formatted_message = f'<div style="text-align: left; margin: 8px 0;"><strong style="color: #f093fb;">🤖 {sender}:</strong><br><span style="background: #f5f5f5; color: #333; padding: 8px 12px; border-radius: 12px; display: inline-block; margin-top: 4px;">{message}</span></div>'
        
        self.chat_display.append(formatted_message)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def show_typing_indicator(self):
        """Show AI typing indicator"""
        self.chat_display.append('<div style="text-align: left; margin: 8px 0;"><span style="background: #f5f5f5; color: #999; padding: 8px 12px; border-radius: 12px; display: inline-block; font-style: italic;">🤖 Assistant is thinking...</span></div>')
        
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def remove_typing_indicator(self):
        """Remove typing indicator"""
        # Get current HTML content
        content = self.chat_display.toHtml()
        
        # Remove typing indicator (last div with thinking message)
        if "Assistant is thinking..." in content:
            lines = content.split('\n')
            # Find and remove the typing indicator line
            filtered_lines = []
            skip_next = False
            for line in lines:
                if "Assistant is thinking..." in line:
                    skip_next = True
                    continue
                if not skip_next:
                    filtered_lines.append(line)
                skip_next = False
            
            self.chat_display.setHtml('\n'.join(filtered_lines))
    
    def add_ai_response(self, response: str):
        """Add AI response to chat"""
        self.remove_typing_indicator()
        self.add_message("Recipe Assistant", response, is_user=False)
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.clear()
        self.chat_history.clear()

class RecipeDetailsView(QWidget):
    """
    Recipe details view with integrated AI chat and proper formatting
    """
    
    # Signals
    back_to_home_requested = Signal()
    like_recipe_requested = Signal(int)
    favorite_recipe_requested = Signal(int)
    chat_message_sent = Signal(str, dict)  # message, recipe_context
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recipe_data = None
        self.setObjectName("RecipeDetailsView")
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup recipe details UI with chat integration"""
        self.setWindowTitle("Recipe Details")
        self.setMinimumSize(700, 500)
        self.setMaximumSize(1000, 700)
        self.resize(900, 650)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with back button
        self.setup_header(main_layout)
        
        # Create splitter for recipe content and chat
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("RecipeDetailsSplitter")
        
        # Recipe content area (left side)
        self.setup_recipe_content(splitter)
        
        # Chat area (right side)
        self.setup_chat_area(splitter)
        
        # Set splitter proportions (70% recipe, 30% chat)
        splitter.setSizes([700, 300])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
    
    def setup_header(self, main_layout):
        """Setup header with navigation"""
        header = QFrame()
        header.setObjectName("RecipeDetailsHeader")
        header.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 20, 8)
        header_layout.setSpacing(16)
        
        # Back button
        back_button = QPushButton("← Back to Recipes")
        back_button.setObjectName("BackButton")
        back_button.clicked.connect(self.back_to_home_requested.emit)
        
        # Title
        self.header_title = QLabel("Recipe Details")
        self.header_title.setObjectName("HeaderTitle")
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
    
    def setup_recipe_content(self, splitter):
        """Setup recipe content area"""
        # Create scroll area for recipe content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setObjectName("RecipeScrollArea")
        
        # Recipe content widget
        content_widget = QWidget()
        content_widget.setObjectName("RecipeContentWidget")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Recipe header with image and basic info
        self.setup_recipe_header(content_layout)
        
        # Recipe details sections
        self.setup_recipe_sections(content_layout)
        
        # Recipe actions
        self.setup_recipe_actions(content_layout)
        
        scroll_area.setWidget(content_widget)
        splitter.addWidget(scroll_area)
    
    def setup_recipe_header(self, layout):
        """Setup recipe header with image and basic info"""
        header_frame = QFrame()
        header_frame.setObjectName("RecipeHeaderFrame")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(20)
        
        # Recipe image
        self.recipe_image = QLabel()
        self.recipe_image.setObjectName("RecipeImage")
        self.recipe_image.setFixedSize(200, 150)
        self.recipe_image.setAlignment(Qt.AlignCenter)
        self.recipe_image.setStyleSheet("""
            QLabel#RecipeImage {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                color: white;
                font-size: 48px;
            }
        """)
        
        # Recipe info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        self.recipe_title = QLabel("Recipe Title")
        self.recipe_title.setObjectName("RecipeTitle")
        
        self.recipe_author = QLabel("By Chef Unknown")
        self.recipe_author.setObjectName("RecipeAuthor")
        
        self.recipe_meta = QLabel("Servings: - | Created: -")
        self.recipe_meta.setObjectName("RecipeMeta")
        
        self.recipe_description = QLabel("Recipe description...")
        self.recipe_description.setObjectName("RecipeDescription")
        self.recipe_description.setWordWrap(True)
        
        info_layout.addWidget(self.recipe_title)
        info_layout.addWidget(self.recipe_author)
        info_layout.addWidget(self.recipe_meta)
        info_layout.addWidget(self.recipe_description)
        info_layout.addStretch()
        
        header_layout.addWidget(self.recipe_image)
        header_layout.addLayout(info_layout)
        
        layout.addWidget(header_frame)
    
    def setup_recipe_sections(self, layout):
        """Setup ingredients and instructions sections"""
        # Ingredients section
        ingredients_frame = QFrame()
        ingredients_frame.setObjectName("IngredientsFrame")
        
        ingredients_layout = QVBoxLayout(ingredients_frame)
        ingredients_layout.setSpacing(12)
        
        ingredients_title = QLabel("🥄 Ingredients")
        ingredients_title.setObjectName("SectionTitle")
        
        self.ingredients_content = QTextEdit()
        self.ingredients_content.setObjectName("IngredientsContent")
        self.ingredients_content.setReadOnly(True)
        self.ingredients_content.setMaximumHeight(150)
        
        ingredients_layout.addWidget(ingredients_title)
        ingredients_layout.addWidget(self.ingredients_content)
        
        # Instructions section
        instructions_frame = QFrame()
        instructions_frame.setObjectName("InstructionsFrame")
        
        instructions_layout = QVBoxLayout(instructions_frame)
        instructions_layout.setSpacing(12)
        
        instructions_title = QLabel("📝 Instructions")
        instructions_title.setObjectName("SectionTitle")
        
        self.instructions_content = QTextEdit()
        self.instructions_content.setObjectName("InstructionsContent")
        self.instructions_content.setReadOnly(True)
        self.instructions_content.setMinimumHeight(200)
        
        instructions_layout.addWidget(instructions_title)
        instructions_layout.addWidget(self.instructions_content)
        
        layout.addWidget(ingredients_frame)
        layout.addWidget(instructions_frame)
    
    def setup_recipe_actions(self, layout):
        """Setup like/favorite buttons"""
        actions_frame = QFrame()
        actions_frame.setObjectName("RecipeActionsFrame")
        
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(12)
        
        self.like_button = QPushButton("♥ Like")
        self.like_button.setObjectName("DetailLikeButton")
        self.like_button.clicked.connect(self.handle_like_clicked)
        
        self.favorite_button = QPushButton("☆ Favorite")
        self.favorite_button.setObjectName("DetailFavoriteButton")
        self.favorite_button.clicked.connect(self.handle_favorite_clicked)
        
        actions_layout.addWidget(self.like_button)
        actions_layout.addWidget(self.favorite_button)
        actions_layout.addStretch()
        
        layout.addWidget(actions_frame)
    
    def setup_chat_area(self, splitter):
        """Setup chat area"""
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.chat_widget.chat_message_sent.connect(self.handle_chat_message)
    


    def format_ingredients(self, ingredients_data: str) -> str:
        """
        Format ingredients from JSON string to readable list
        
        Args:
            ingredients_data (str): JSON string or plain text
            
        Returns:
            str: Formatted ingredients text
        """
        if not ingredients_data:
            return "No ingredients listed"
        
        try:
            # Try to parse as JSON first
            ingredients_list = json.loads(ingredients_data)
            if isinstance(ingredients_list, list):
                # Create numbered list
                formatted = []
                for i, ingredient in enumerate(ingredients_list, 1):
                    # Decode HTML entities and clean up extra spaces
                    clean_ingredient = html.unescape(str(ingredient))
                    clean_ingredient = ' '.join(clean_ingredient.split())  # Remove extra whitespace
                    formatted.append(f"{i}. {clean_ingredient}")
                return "\n".join(formatted)
            else:
                # If it's not a list, return as is
                return html.unescape(str(ingredients_list))
        except (json.JSONDecodeError, TypeError):
            # If JSON fails, try Python literal evaluation for mixed quotes
            try:
                ingredients_list = ast.literal_eval(ingredients_data)
                if isinstance(ingredients_list, list):
                    formatted = []
                    for i, ingredient in enumerate(ingredients_list, 1):
                        clean_ingredient = html.unescape(str(ingredient))
                        clean_ingredient = ' '.join(clean_ingredient.split())
                        formatted.append(f"{i}. {clean_ingredient}")
                    return "\n".join(formatted)
            except (ValueError, SyntaxError):
                pass
            
            # If all parsing fails, treat as plain text
            return html.unescape(str(ingredients_data))

    def format_instructions(self, instructions_data: str) -> str:
        """
        Format instructions from JSON string to readable steps
        
        Args:
            instructions_data (str): JSON string or plain text
            
        Returns:
            str: Formatted instructions text
        """
        if not instructions_data:
            return "No instructions provided"
        
        print(f"DEBUG: Trying to format instructions: {repr(instructions_data)}")
        
        try:
            # Try to parse as JSON first
            instructions_list = json.loads(instructions_data)
            print(f"DEBUG: JSON parsing succeeded, type: {type(instructions_list)}")
            if isinstance(instructions_list, list):
                # Create numbered steps
                formatted = []
                for i, instruction in enumerate(instructions_list, 1):
                    # Decode HTML entities and clean up
                    clean_instruction = html.unescape(str(instruction))
                    clean_instruction = ' '.join(clean_instruction.split())  # Remove extra whitespace
                    formatted.append(f"Step {i}:\n{clean_instruction}\n")
                return "\n".join(formatted)
            else:
                # If it's not a list, return as is
                return html.unescape(str(instructions_list))
        except (json.JSONDecodeError, TypeError) as e:
            print(f"DEBUG: JSON parsing failed: {e}")
            # If JSON fails, try Python literal evaluation for mixed quotes
            try:
                print("DEBUG: Trying ast.literal_eval")
                instructions_list = ast.literal_eval(instructions_data)
                print(f"DEBUG: ast.literal_eval succeeded, type: {type(instructions_list)}")
                if isinstance(instructions_list, list):
                    formatted = []
                    for i, instruction in enumerate(instructions_list, 1):
                        clean_instruction = html.unescape(str(instruction))
                        clean_instruction = ' '.join(clean_instruction.split())
                        formatted.append(f"Step {i}:\n{clean_instruction}\n")
                    result = "\n".join(formatted)
                    print(f"DEBUG: Final formatted result: {repr(result)}")
                    return result
            except (ValueError, SyntaxError) as e:
                print(f"DEBUG: ast.literal_eval failed: {e}")
            
            # If all parsing fails, treat as plain text
            return html.unescape(str(instructions_data))
    
    def set_recipe_data(self, recipe_data: dict):
        """Set recipe data and update display"""
        self.recipe_data = recipe_data
        self.update_recipe_display()
    
    def update_recipe_display(self):
        """Update recipe display with data"""
        if not self.recipe_data:
            return
        
        # Update header
        title = self.recipe_data.get('title', 'Untitled Recipe')
        self.header_title.setText(f"Recipe: {title}")
        
        # Update recipe info
        self.recipe_title.setText(title)
        self.recipe_author.setText(f"By Chef {self.recipe_data.get('author_name', 'Unknown')}")
        
        servings = self.recipe_data.get('servings', 'Unknown')
        created_at = self.recipe_data.get('created_at', 'Unknown')
        self.recipe_meta.setText(f"Servings: {servings} | Created: {created_at}")
        
        self.recipe_description.setText(self.recipe_data.get('description', 'No description available'))
        
        # DEBUG: Print raw data
        ingredients_raw = self.recipe_data.get('ingredients', '')
        instructions_raw = self.recipe_data.get('instructions', '')
        
        print("DEBUG: Raw ingredients data:")
        print(f"Type: {type(ingredients_raw)}")
        print(f"Value: {repr(ingredients_raw)}")
        
        print("DEBUG: Raw instructions data:")
        print(f"Type: {type(instructions_raw)}")
        print(f"Value: {repr(instructions_raw)}")
        
        # Update ingredients with formatting
        formatted_ingredients = self.format_ingredients(ingredients_raw)
        print(f"DEBUG: Formatted ingredients: {repr(formatted_ingredients)}")
        self.ingredients_content.setPlainText(formatted_ingredients)
        
        # Update instructions with formatting
        formatted_instructions = self.format_instructions(instructions_raw)
        print(f"DEBUG: Formatted instructions: {repr(formatted_instructions)}")
        self.instructions_content.setPlainText(formatted_instructions)
        
        # Update buttons
        likes_count = self.recipe_data.get('likes_count', 0)
        is_liked = self.recipe_data.get('is_liked', False)
        is_favorited = self.recipe_data.get('is_favorited', False)
        
        self.like_button.setText(f"{'♥' if is_liked else '♡'} {likes_count}")
        self.favorite_button.setText("★" if is_favorited else "☆")
        
        # Update image placeholder
        if self.recipe_data.get('image_url'):
            self.recipe_image.setText("🍽️")
        else:
            self.recipe_image.setText("📸")
        
        # Clear chat for new recipe
        self.chat_widget.clear_chat()
    
    def handle_like_clicked(self):
        """Handle like button click"""
        if self.recipe_data:
            recipe_id = self.recipe_data.get('recipe_id')
            if recipe_id:
                self.like_recipe_requested.emit(recipe_id)
    
    def handle_favorite_clicked(self):
        """Handle favorite button click"""
        if self.recipe_data:
            recipe_id = self.recipe_data.get('recipe_id')
            if recipe_id:
                self.favorite_recipe_requested.emit(recipe_id)
    
    def handle_chat_message(self, message: str):
        """Handle chat message with recipe context"""
        if self.recipe_data:
            # Create recipe context for AI
            recipe_context = {
                'title': self.recipe_data.get('title', ''),
                'description': self.recipe_data.get('description', ''),
                'ingredients': self.format_ingredients(self.recipe_data.get('ingredients', '')),
                'instructions': self.format_instructions(self.recipe_data.get('instructions', '')),
                'servings': self.recipe_data.get('servings', ''),
                'author_name': self.recipe_data.get('author_name', '')
            }
            
            self.chat_message_sent.emit(message, recipe_context)
    
    def add_ai_response(self, response: str):
        """Add AI response to chat"""
        self.chat_widget.add_ai_response(response)
    
    def update_like_status(self, is_liked: bool, likes_count: int):
        """Update like button status"""
        if self.recipe_data:
            self.recipe_data['is_liked'] = is_liked
            self.recipe_data['likes_count'] = likes_count
            self.like_button.setText(f"{'♥' if is_liked else '♡'} {likes_count}")
    
    def update_favorite_status(self, is_favorited: bool):
        """Update favorite button status"""
        if self.recipe_data:
            self.recipe_data['is_favorited'] = is_favorited
            self.favorite_button.setText("★" if is_favorited else "☆")