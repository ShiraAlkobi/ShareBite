from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Any

class RecipeFormModel(QObject):
    """Recipe form data model"""
    
    form_valid = Signal(bool)
    field_error = Signal(str, str)
    
    def __init__(self):
        print("יוצר RecipeFormModel")  
        super().__init__()
        self.recipe_data = {
            'title': '',
            'description': '',
            'ingredients': [],
            'instructions': [],
            'prep_time': 0,
            'cook_time': 0,
            'servings': 1,
            'difficulty': 'easy',
            'tags': [],
            'image_url': ''
        }
        self.is_editing = False
        self.editing_recipe_id = None
        
    def update_field(self, field_name: str, value):
        """Update field value"""
        self.recipe_data[field_name] = value
        
    def get_field(self, field_name: str):
        """Get field value"""
        return self.recipe_data.get(field_name)
        
    def validate_form(self) -> bool:
        """Validate form"""
        return True  # Simplified for now
        
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data"""
        return self.recipe_data.copy()
        
    def reset_form(self):
        """Reset form"""
        self.__init__()
        
    def set_recipe_data(self, data: Dict[str, Any]):
        """Set recipe data"""
        self.recipe_data.update(data)
        
    def add_ingredient(self, ingredient: str):
        """Add ingredient"""
        if ingredient not in self.recipe_data['ingredients']:
            self.recipe_data['ingredients'].append(ingredient)
            
    def add_instruction(self, instruction: str):
        """Add instruction"""
        self.recipe_data['instructions'].append(instruction)
        
    def add_tag(self, tag: str):
        """Add tag"""
        if tag not in self.recipe_data['tags']:
            self.recipe_data['tags'].append(tag)
            
    def remove_tag(self, tag: str):
        """Remove tag"""
        if tag in self.recipe_data['tags']:
            self.recipe_data['tags'].remove(tag)