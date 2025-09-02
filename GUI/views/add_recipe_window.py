"""
Add Recipe Window - Recipe Creation and Editing Form
Implements MVP pattern - View layer for recipe form management
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QFrame, QGridLayout, QTextEdit,
    QSpinBox, QComboBox, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QProgressBar, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter
from services.api_service import APIManager
from typing import Dict, List, Any, Optional
from models.recipe_form_model import RecipeFormModel

class TagWidget(QFrame):
    """Widget for displaying and managing tags"""
    
    tag_removed = Signal(str)
    
    def __init__(self, tag_name: str):
        super().__init__()
        self.tag_name = tag_name
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Tag label
        tag_label = QLabel(self.tag_name)
        tag_label.setObjectName("tagLabel")
        layout.addWidget(tag_label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setObjectName("tagRemoveButton")
        remove_btn.setFixedSize(20, 20)
        remove_btn.clicked.connect(lambda: self.tag_removed.emit(self.tag_name))
        layout.addWidget(remove_btn)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 12px;
                margin: 2px;
            }
            QLabel#tagLabel {
                color: #1976d2;
                font-size: 9pt;
            }
            QPushButton#tagRemoveButton {
                background-color: #f44336;
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
            }
        """)


class AddRecipeWindow(QWidget):
    """
    Recipe creation and editing window
    Supports both new recipe creation and editing existing recipes
    """
    
    # Signals
    recipe_created = Signal(dict)    # recipe_data
    recipe_updated = Signal(dict)    # recipe_data
    back_to_home = Signal()
    
    def __init__(self, api_service, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.api_manager = APIManager(api_service)
        self.form_model = RecipeFormModel()  # הוסף שורה זו

        self.selected_image_path = None
        self.is_editing = False
        self.editing_recipe_id = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup add recipe UI"""
        self.setObjectName("AddRecipeWindow")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        self.setup_header(main_layout)
        
        # Form content
        self.setup_form_content(main_layout)
        
        # Footer buttons
        self.setup_footer_buttons(main_layout)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setVisible(False)
        self.loading_bar.setRange(0, 0)
        main_layout.addWidget(self.loading_bar)
        
        # Apply styling
        self.setStyleSheet(self.setup_theme())
        
    def setup_header(self, main_layout):
        """Setup form header"""
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← חזור")
        self.back_button.setObjectName("backButton")
        header_layout.addWidget(self.back_button)
        
        # Title
        self.form_title = QLabel("הוסף מתכון חדש")
        self.form_title.setObjectName("formTitle")
        header_layout.addWidget(self.form_title)
        
        header_layout.addStretch()
        
        # Save draft button
        self.save_draft_button = QPushButton("שמור טיוטה")
        self.save_draft_button.setObjectName("draftButton")
        header_layout.addWidget(self.save_draft_button)
        
        main_layout.addLayout(header_layout)
        
    def setup_form_content(self, main_layout):
        """Setup main form content"""
        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setObjectName("formScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Form widget
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(20)
        
        # Basic info section
        self.setup_basic_info_section(form_layout)
        
        # Image section
        self.setup_image_section(form_layout)
        
        # Ingredients section
        self.setup_ingredients_section(form_layout)
        
        # Instructions section
        self.setup_instructions_section(form_layout)
        
        # Tags section
        self.setup_tags_section(form_layout)
        
        # Time and servings section
        self.setup_time_servings_section(form_layout)
        
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)
        
    def setup_basic_info_section(self, form_layout):
        """Setup basic recipe information section"""
        basic_group = QGroupBox("מידע בסיסי")
        basic_group.setObjectName("formGroup")
        basic_layout = QVBoxLayout(basic_group)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.addWidget(QLabel("כותרת המתכון *"))
        self.title_input = QLineEdit()
        self.title_input.setObjectName("titleInput")
        self.title_input.setPlaceholderText("הכניסו כותרת למתכון...")
        title_layout.addWidget(self.title_input)
        basic_layout.addLayout(title_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("תיאור המתכון *"))
        self.description_input = QTextEdit()
        self.description_input.setObjectName("descriptionInput")
        self.description_input.setPlaceholderText("תארו את המתכון, המקור שלו, או סיפור מיוחד...")
        self.description_input.setMaximumHeight(100)
        desc_layout.addWidget(self.description_input)
        basic_layout.addLayout(desc_layout)
        
        # Difficulty
        difficulty_layout = QHBoxLayout()
        difficulty_layout.addWidget(QLabel("רמת קושי:"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.setObjectName("difficultyCombo")
        self.difficulty_combo.addItems(["קל", "בינוני", "קשה"])
        self.difficulty_combo.setCurrentText("קל")
        difficulty_layout.addWidget(self.difficulty_combo)
        difficulty_layout.addStretch()
        basic_layout.addLayout(difficulty_layout)
        
        form_layout.addWidget(basic_group)
        
    def setup_image_section(self, form_layout):
        """Setup image upload section"""
        image_group = QGroupBox("תמונת המתכון")
        image_group.setObjectName("formGroup")
        image_layout = QVBoxLayout(image_group)
        
        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setObjectName("imagePreview")
        self.image_preview.setFixedSize(300, 200)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setText("לחץ לבחירת תמונה")
        self.image_preview.setStyleSheet("""
            QLabel#imagePreview {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #666;
            }
        """)
        image_layout.addWidget(self.image_preview, alignment=Qt.AlignCenter)
        
        # Image buttons
        image_buttons_layout = QHBoxLayout()
        self.select_image_button = QPushButton("בחר תמונה")
        self.select_image_button.setObjectName("selectImageButton")
        image_buttons_layout.addWidget(self.select_image_button)
        
        self.remove_image_button = QPushButton("הסר תמונה")
        self.remove_image_button.setObjectName("removeImageButton")
        self.remove_image_button.setVisible(False)
        image_buttons_layout.addWidget(self.remove_image_button)
        
        image_buttons_layout.addStretch()
        image_layout.addLayout(image_buttons_layout)
        
        form_layout.addWidget(image_group)
        
    def setup_ingredients_section(self, form_layout):
        """Setup ingredients input section"""
        ingredients_group = QGroupBox("מרכיבים *")
        ingredients_group.setObjectName("formGroup")
        ingredients_layout = QVBoxLayout(ingredients_group)
        
        # Ingredients input
        ingredients_input_layout = QHBoxLayout()
        self.ingredient_input = QLineEdit()
        self.ingredient_input.setObjectName("ingredientInput")
        self.ingredient_input.setPlaceholderText("הכניסו מרכיב (לדוגמה: 2 כפות שמן זית)")
        ingredients_input_layout.addWidget(self.ingredient_input)
        
        self.add_ingredient_button = QPushButton("הוסף")
        self.add_ingredient_button.setObjectName("addButton")
        ingredients_input_layout.addWidget(self.add_ingredient_button)
        
        ingredients_layout.addLayout(ingredients_input_layout)
        
        # Ingredients list
        self.ingredients_list = QListWidget()
        self.ingredients_list.setObjectName("ingredientsList")
        self.ingredients_list.setMaximumHeight(150)
        ingredients_layout.addWidget(self.ingredients_list)
        
        form_layout.addWidget(ingredients_group)
        
    def setup_instructions_section(self, form_layout):
        """Setup instructions input section"""
        instructions_group = QGroupBox("הוראות הכנה *")
        instructions_group.setObjectName("formGroup")
        instructions_layout = QVBoxLayout(instructions_group)
        
        # Instructions input
        instructions_input_layout = QHBoxLayout()
        self.instruction_input = QTextEdit()
        self.instruction_input.setObjectName("instructionInput")
        self.instruction_input.setPlaceholderText("הכניסו שלב הכנה...")
        self.instruction_input.setMaximumHeight(80)
        instructions_input_layout.addWidget(self.instruction_input)
        
        instruction_btn_layout = QVBoxLayout()
        self.add_instruction_button = QPushButton("הוסף שלב")
        self.add_instruction_button.setObjectName("addButton")
        instruction_btn_layout.addWidget(self.add_instruction_button)
        instruction_btn_layout.addStretch()
        instructions_input_layout.addLayout(instruction_btn_layout)
        
        instructions_layout.addLayout(instructions_input_layout)
        
        # Instructions list
        self.instructions_list = QListWidget()
        self.instructions_list.setObjectName("instructionsList")
        self.instructions_list.setMaximumHeight(200)
        instructions_layout.addWidget(self.instructions_list)
        
        form_layout.addWidget(instructions_group)
        
    def setup_tags_section(self, form_layout):
        """Setup tags input section"""
        tags_group = QGroupBox("תגיות")
        tags_group.setObjectName("formGroup")
        tags_layout = QVBoxLayout(tags_group)
        
        # Tags input
        tags_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("tagInput")
        self.tag_input.setPlaceholderText("הכניסו תגית (לדוגמה: טבעוני, קינוח, ארוחת בוקר)")
        tags_input_layout.addWidget(self.tag_input)
        
        self.add_tag_button = QPushButton("הוסף תגית")
        self.add_tag_button.setObjectName("addButton")
        tags_input_layout.addWidget(self.add_tag_button)
        
        tags_layout.addLayout(tags_input_layout)
        
        # Tags display area
        self.tags_scroll_area = QScrollArea()
        self.tags_scroll_area.setObjectName("tagsScrollArea")
        self.tags_scroll_area.setMaximumHeight(100)
        self.tags_scroll_area.setWidgetResizable(True)
        
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setAlignment(Qt.AlignLeft)
        
        self.tags_scroll_area.setWidget(self.tags_container)
        tags_layout.addWidget(self.tags_scroll_area)
        
        form_layout.addWidget(tags_group)
        
    def setup_time_servings_section(self, form_layout):
        """Setup time and servings section"""
        time_group = QGroupBox("זמן ומנות")
        time_group.setObjectName("formGroup")
        time_layout = QGridLayout(time_group)
        
        # Prep time
        time_layout.addWidget(QLabel("זמן הכנה (דקות):"), 0, 0)
        self.prep_time_input = QSpinBox()
        self.prep_time_input.setObjectName("timeInput")
        self.prep_time_input.setRange(0, 999)
        self.prep_time_input.setSuffix(" דק'")
        time_layout.addWidget(self.prep_time_input, 0, 1)
        
        # Cook time
        time_layout.addWidget(QLabel("זמן בישול (דקות):"), 0, 2)
        self.cook_time_input = QSpinBox()
        self.cook_time_input.setObjectName("timeInput")
        self.cook_time_input.setRange(0, 999)
        self.cook_time_input.setSuffix(" דק'")
        time_layout.addWidget(self.cook_time_input, 0, 3)
        
        # Servings
        time_layout.addWidget(QLabel("מספר מנות:"), 1, 0)
        self.servings_input = QSpinBox()
        self.servings_input.setObjectName("servingsInput")
        self.servings_input.setRange(1, 50)
        self.servings_input.setValue(4)
        self.servings_input.setSuffix(" מנות")
        time_layout.addWidget(self.servings_input, 1, 1)
        
        form_layout.addWidget(time_group)
        
    def setup_footer_buttons(self, main_layout):
        """Setup footer action buttons"""
        footer_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("בטל")
        self.cancel_button.setObjectName("cancelButton")
        footer_layout.addWidget(self.cancel_button)
        
        footer_layout.addStretch()
        
        # Preview button
        self.preview_button = QPushButton("תצוגה מקדימה")
        self.preview_button.setObjectName("previewButton")
        footer_layout.addWidget(self.preview_button)
        
        # Save button
        self.save_button = QPushButton("שמור מתכון")
        self.save_button.setObjectName("saveButton")
        footer_layout.addWidget(self.save_button)
        
        main_layout.addLayout(footer_layout)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Navigation
        self.back_button.clicked.connect(self.back_to_home.emit)
        self.cancel_button.clicked.connect(self.back_to_home.emit)
        
        # Form actions
        self.save_button.clicked.connect(self.handle_save_recipe)
        self.save_draft_button.clicked.connect(self.handle_save_draft)
        self.preview_button.clicked.connect(self.handle_preview)
        
        # Image actions
        self.select_image_button.clicked.connect(self.handle_select_image)
        self.remove_image_button.clicked.connect(self.handle_remove_image)
        self.image_preview.mousePressEvent = lambda event: self.handle_select_image()
        
        # Add buttons
        self.add_ingredient_button.clicked.connect(self.handle_add_ingredient)
        self.add_instruction_button.clicked.connect(self.handle_add_instruction)
        self.add_tag_button.clicked.connect(self.handle_add_tag)
        
        # Enter key support
        self.ingredient_input.returnPressed.connect(self.handle_add_ingredient)
        self.tag_input.returnPressed.connect(self.handle_add_tag)
        
        # Form validation
        self.title_input.textChanged.connect(self.validate_form)
        self.description_input.textChanged.connect(self.validate_form)
        
        # Model signals
        self.form_model.form_valid.connect(self.on_form_validation_changed)
        self.form_model.field_error.connect(self.on_field_error)
        
    def handle_save_recipe(self):
        """Handle save recipe button click"""
        if not self.validate_and_collect_data():
            return
            
        self.set_loading(True)
        
        # Prepare recipe data
        recipe_data = self.form_model.get_form_data()
        
        # Handle image file
        image_file = None
        if self.selected_image_path:
            try:
                with open(self.selected_image_path, 'rb') as f:
                    image_file = f.read()
            except Exception as e:
                QMessageBox.warning(self, "שגיאה", f"שגיאה בקריאת התמונה: {e}")
                self.set_loading(False)
                return
        
        # Choose API method based on editing mode
        if self.is_editing:
            api_method = 'update_recipe'
            kwargs = {'recipe_id': self.editing_recipe_id, 'recipe_data': recipe_data}
            success_callback = self.on_recipe_updated
        else:
            api_method = 'create_recipe'
            kwargs = {'recipe_data': recipe_data}
            success_callback = self.on_recipe_created
            
        # Add image if available
        if image_file:
            kwargs['image_file'] = image_file
            
        # Make API call
        self.api_manager.call_api(
            api_method,
            success_callback=success_callback,
            error_callback=self.on_save_error,
            **kwargs
        )
        
    def handle_save_draft(self):
        """Handle save draft button click"""
        # For now, just show a message
        QMessageBox.information(self, "טיוטה נשמרה", "הטיוטה נשמרה בהצלחה!")
        
    def handle_preview(self):
        """Handle preview button click"""
        if not self.validate_and_collect_data():
            return
            
        # Create preview dialog/window
        QMessageBox.information(self, "תצוגה מקדימה", "תצוגה מקדימה תהיה זמינה בקרוב!")
        
    def handle_select_image(self):
        """Handle image selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "בחר תמונה למתכון",
            "",
            "תמונות (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            self.selected_image_path = file_path
            
            # Load and display preview
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale image to fit preview
                scaled_pixmap = pixmap.scaled(
                    self.image_preview.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_preview.setPixmap(scaled_pixmap)
                self.remove_image_button.setVisible(True)
            else:
                QMessageBox.warning(self, "שגיאה", "לא ניתן לטעון את התמונה")
                
    def handle_remove_image(self):
        """Handle image removal"""
        self.selected_image_path = None
        self.image_preview.clear()
        self.image_preview.setText("לחץ לבחירת תמונה")
        self.remove_image_button.setVisible(False)
        
    def handle_add_ingredient(self):
        """Handle add ingredient"""
        ingredient = self.ingredient_input.text().strip()
        if not ingredient:
            return
            
        # Add to model
        self.form_model.add_ingredient(ingredient)
        
        # Add to UI
        item = QListWidgetItem(ingredient)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.ingredients_list.addItem(item)
        
        # Clear input
        self.ingredient_input.clear()
        self.ingredient_input.setFocus()
        
    def handle_add_instruction(self):
        """Handle add instruction"""
        instruction = self.instruction_input.toPlainText().strip()
        if not instruction:
            return
            
        # Add to model
        self.form_model.add_instruction(instruction)
        
        # Add to UI with step number
        step_num = self.instructions_list.count() + 1
        item = QListWidgetItem(f"{step_num}. {instruction}")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.instructions_list.addItem(item)
        
        # Clear input
        self.instruction_input.clear()
        self.instruction_input.setFocus()
        
    def handle_add_tag(self):
        """Handle add tag"""
        tag = self.tag_input.text().strip()
        if not tag:
            return
            
        # Add to model
        self.form_model.add_tag(tag)
        
        # Add to UI
        tag_widget = TagWidget(tag)
        tag_widget.tag_removed.connect(self.handle_remove_tag)
        self.tags_layout.addWidget(tag_widget)
        
        # Clear input
        self.tag_input.clear()
        self.tag_input.setFocus()
        
    def handle_remove_tag(self, tag_name: str):
        """Handle tag removal"""
        # Remove from model
        self.form_model.remove_tag(tag_name)
        
        # Remove from UI
        for i in range(self.tags_layout.count()):
            widget = self.tags_layout.itemAt(i).widget()
            if isinstance(widget, TagWidget) and widget.tag_name == tag_name:
                widget.deleteLater()
                break
                
    def validate_and_collect_data(self) -> bool:
        """Validate form and collect data"""
        # Update model with current form data
        self.form_model.update_field('title', self.title_input.text())
        self.form_model.update_field('description', self.description_input.toPlainText())
        
        # Convert difficulty to English
        difficulty_map = {"קל": "easy", "בינוני": "medium", "קשה": "hard"}
        difficulty = difficulty_map.get(self.difficulty_combo.currentText(), "easy")
        self.form_model.update_field('difficulty', difficulty)
        
        self.form_model.update_field('prep_time', self.prep_time_input.value())
        self.form_model.update_field('cook_time', self.cook_time_input.value())
        self.form_model.update_field('servings', self.servings_input.value())
        
        # Validate form
        return self.form_model.validate_form()
        
    def on_recipe_created(self, result: Dict[str, Any]):
        """Handle successful recipe creation"""
        self.set_loading(False)
        recipe_data = result.get('recipe', {})
        self.recipe_created.emit(recipe_data)
        
    def on_recipe_updated(self, result: Dict[str, Any]):
        """Handle successful recipe update"""
        self.set_loading(False)
        recipe_data = result.get('recipe', {})
        self.recipe_updated.emit(recipe_data)
        
    def on_save_error(self, error: str):
        """Handle save error"""
        self.set_loading(False)
        QMessageBox.warning(self, "שגיאה בשמירה", f"שגיאה בשמירת המתכון: {error}")
        
    def on_form_validation_changed(self, is_valid: bool):
        """Handle form validation change"""
        self.save_button.setEnabled(is_valid)
        
    def on_field_error(self, field_name: str, error_message: str):
        """Handle field validation error"""
        QMessageBox.warning(self, "שגיאת תקינות", error_message)
        
    def validate_form(self):
        """Trigger form validation"""
        self.validate_and_collect_data()
        
    def reset_form(self):
        """Reset form to empty state"""
        self.form_model.reset_form()
        self.is_editing = False
        self.editing_recipe_id = None
        
        # Clear UI
        self.form_title.setText("הוסף מתכון חדש")
        self.title_input.clear()
        self.description_input.clear()
        self.difficulty_combo.setCurrentIndex(0)
        self.prep_time_input.setValue(0)
        self.cook_time_input.setValue(0)
        self.servings_input.setValue(4)
        
        self.ingredient_input.clear()
        self.instruction_input.clear()
        self.tag_input.clear()
        
        self.ingredients_list.clear()
        self.instructions_list.clear()
        
        # Clear tags
        while self.tags_layout.count():
            child = self.tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Clear image
        self.handle_remove_image()
        
    def load_recipe_for_edit(self, recipe_id: int):
        """Load recipe data for editing"""
        self.is_editing = True
        self.editing_recipe_id = recipe_id
        self.form_title.setText("ערוך מתכון")
        
        # Load recipe data from API
        self.set_loading(True)
        self.api_manager.call_api(
            'get_recipe_by_id',
            success_callback=self.on_edit_recipe_loaded,
            error_callback=self.on_edit_load_error,
            recipe_id=recipe_id
        )
        
    def on_edit_recipe_loaded(self, result: Dict[str, Any]):
        """Handle recipe loaded for editing"""
        self.set_loading(False)
        
        recipe = result.get('recipe', {})
        if not recipe:
            QMessageBox.warning(self, "שגיאה", "לא ניתן לטעון את המתכון לעריכה")
            return
            
        # Populate form with recipe data
        self.title_input.setText(recipe.get('title', ''))
        self.description_input.setPlainText(recipe.get('description', ''))
        
        # Set difficulty
        difficulty_map = {"easy": "קל", "medium": "בינוני", "hard": "קשה"}
        difficulty = difficulty_map.get(recipe.get('difficulty', 'easy'), "קל")
        self.difficulty_combo.setCurrentText(difficulty)
        
        self.prep_time_input.setValue(recipe.get('prep_time', 0))
        self.cook_time_input.setValue(recipe.get('cook_time', 0))
        self.servings_input.setValue(recipe.get('servings', 1))
        
        # Load ingredients
        ingredients = recipe.get('ingredients', [])
        for ingredient in ingredients:
            self.form_model.add_ingredient(ingredient)
            item = QListWidgetItem(ingredient)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.ingredients_list.addItem(item)
            
        # Load instructions
        instructions = recipe.get('instructions', [])
        for instruction in instructions:
            self.form_model.add_instruction(instruction)
            step_num = self.instructions_list.count() + 1
            item = QListWidgetItem(f"{step_num}. {instruction}")
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.instructions_list.addItem(item)
            
        # Load tags
        tags = recipe.get('tags', [])
        for tag in tags:
            self.form_model.add_tag(tag)
            tag_widget = TagWidget(tag)
            tag_widget.tag_removed.connect(self.handle_remove_tag)
            self.tags_layout.addWidget(tag_widget)
            
        # Load image if available
        image_url = recipe.get('image_url', '')
        if image_url:
            # For editing, we show that there's an existing image
            # but don't download it for preview (can be added later)
            self.image_preview.setText(f"תמונה קיימת:\n{image_url}")
            
        # Update form model
        self.form_model.set_recipe_data(recipe)
        
    def on_edit_load_error(self, error: str):
        """Handle error loading recipe for edit"""
        self.set_loading(False)
        QMessageBox.warning(self, "שגיאה", f"שגיאה בטעינת המתכון: {error}")
        self.back_to_home.emit()
        
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.loading_bar.setVisible(loading)
        
        # Disable/enable form controls
        controls = [
            self.title_input, self.description_input, self.difficulty_combo,
            self.prep_time_input, self.cook_time_input, self.servings_input,
            self.ingredient_input, self.instruction_input, self.tag_input,
            self.save_button, self.save_draft_button, self.preview_button,
            self.select_image_button, self.add_ingredient_button,
            self.add_instruction_button, self.add_tag_button
        ]
        
        for control in controls:
            control.setEnabled(not loading)
            
        if loading:
            self.save_button.setText("שומר...")
        else:
            self.save_button.setText("שמור מתכון")
            
    def setup_theme(self):
        """Setup application theme and styling"""
        return """
            QWidget#AddRecipeWindow {
                background-color: #f7fafc;
            }
            
            QLabel#formTitle {
                font-size: 22pt;
                font-weight: 700;
                color: #2d3748;
                padding: 8px 0;
            }
            
            QPushButton#backButton {
                background-color: #a0aec0;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#backButton:hover {
                background-color: #718096;
            }
            
            QPushButton#draftButton {
                background-color: #ed8936;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#draftButton:hover {
                background-color: #dd6b20;
            }
            
            QGroupBox#formGroup {
                font-size: 11pt;
                font-weight: 600;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 12px;
                background-color: white;
            }
            
            QGroupBox#formGroup::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }
            
            QLineEdit#titleInput {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 11pt;
                color: #2d3748;
            }
            
            QLineEdit#titleInput:focus {
                border-color: #4299e1;
            }
            
            QTextEdit#descriptionInput, QTextEdit#instructionInput {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                color: #2d3748;
            }
            
            QTextEdit#descriptionInput:focus, QTextEdit#instructionInput:focus {
                border-color: #4299e1;
            }
            
            QPushButton#selectImageButton {
                background-color: #4299e1;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#selectImageButton:hover {
                background-color: #3182ce;
            }
            
            QPushButton#removeImageButton {
                background-color: #f56565;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#removeImageButton:hover {
                background-color: #e53e3e;
            }
            
            QLineEdit#ingredientInput, QLineEdit#tagInput {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 10pt;
            }
            
            QLineEdit#ingredientInput:focus, QLineEdit#tagInput:focus {
                border-color: #4299e1;
            }
            
            QPushButton#addButton {
                background-color: #48bb78;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
                font-weight: 600;
            }
            
            QPushButton#addButton:hover {
                background-color: #38a169;
            }
            
            QListWidget#ingredientsList, QListWidget#instructionsList {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
                font-size: 10pt;
            }
            
            QListWidget#ingredientsList::item, QListWidget#instructionsList::item {
                padding: 6px;
                border-bottom: 1px solid #edf2f7;
                border-radius: 3px;
                margin: 1px 0;
            }
            
            QListWidget#ingredientsList::item:hover, QListWidget#instructionsList::item:hover {
                background-color: #f7fafc;
            }
            
            QSpinBox#timeInput, QSpinBox#servingsInput {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px;
                font-size: 10pt;
                min-width: 70px;
            }
            
            QSpinBox#timeInput:focus, QSpinBox#servingsInput:focus {
                border-color: #4299e1;
            }
            
            QPushButton#cancelButton {
                background-color: #a0aec0;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 10px 18px;
                min-width: 90px;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #718096;
            }
            
            QPushButton#previewButton {
                background-color: #4299e1;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 10px 18px;
                min-width: 110px;
            }
            
            QPushButton#previewButton:hover {
                background-color: #3182ce;
            }
            
            QPushButton#saveButton {
                background-color: #48bb78;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 11pt;
                font-weight: 700;
                padding: 12px 20px;
                min-width: 140px;
            }
            
            QPushButton#saveButton:hover {
                background-color: #38a169;
            }
            
            QPushButton#saveButton:disabled {
                background-color: #a0aec0;
                color: #718096;
            }
            
            QScrollArea#formScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QProgressBar#loadingBar {
                border: none;
                border-radius: 4px;
                background-color: #edf2f7;
                height: 6px;
            }
            
            QProgressBar#loadingBar::chunk {
                background-color: #48bb78;
                border-radius: 3px;
            }
        """