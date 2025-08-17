from typing import Any, Dict
from datetime import datetime
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib

class BaseModel:
    """
    Base model class with common functionality
    """
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        instance = cls()
        for key, value in data.items():
            # Convert SQL Server column names to Python attributes
            attr_name = key.lower()
            if hasattr(instance, attr_name):
                setattr(instance, attr_name, value)
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result