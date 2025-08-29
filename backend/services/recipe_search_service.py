import requests
from typing import List, Dict, Any
from database import execute_query
import re

class RecipeSearchService:
    """
    Focused service for searching recipes in database - NO AI logic here
    """
    
    def search_recipes_by_exact_match(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Search for exact recipe matches first (highest priority)
        """
        try:
            query_clean = query.lower().strip()
            
            # Search for exact phrase in title first (highest relevance)
            sql = f"""
            SELECT TOP {limit}
                r.RecipeID, r.Title, r.Description, r.Ingredients,
                r.Instructions, r.RawIngredients, r.Servings,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
                100 as RelevanceScore
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE r.Title LIKE ?
            ORDER BY LikesCount DESC
            """
            
            exact_pattern = f"%{query_clean}%"
            results = execute_query(sql, (exact_pattern,))
            
            if results:
                print(f"Found {len(results)} exact title matches for '{query_clean}'")
                return results
            
            # If no title matches, try ingredients
            sql = f"""
            SELECT TOP {limit}
                r.RecipeID, r.Title, r.Description, r.Ingredients,
                r.Instructions, r.RawIngredients, r.Servings,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
                80 as RelevanceScore
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE r.Ingredients LIKE ? OR r.RawIngredients LIKE ?
            ORDER BY LikesCount DESC
            """
            
            results = execute_query(sql, (exact_pattern, exact_pattern))
            print(f"Found {len(results)} ingredient matches for '{query_clean}'")
            return results
            
        except Exception as e:
            print(f"Error in exact search: {e}")
            return []
    
    def search_recipes_by_keywords(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Fallback keyword search with better relevance scoring
        """
        try:
            keywords = self._extract_smart_keywords(query)
            if not keywords:
                return self.get_popular_recipes(limit)
            
            # Build search with multiple keyword combinations
            conditions = []
            params = []
            
            # Main keyword (most important)
            main_keyword = keywords[0]
            conditions.append("(r.Title LIKE ? OR r.Ingredients LIKE ?)")
            params.extend([f"%{main_keyword}%", f"%{main_keyword}%"])
            
            # Secondary keywords if available
            if len(keywords) > 1:
                for keyword in keywords[1:min(3, len(keywords))]:  # Max 3 keywords
                    conditions.append("(r.Title LIKE ? OR r.Ingredients LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            sql = f"""
            SELECT TOP {limit}
                r.RecipeID, r.Title, r.Description, r.Ingredients,
                r.Instructions, r.RawIngredients, r.Servings,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE {' AND '.join(conditions)}
            ORDER BY LikesCount DESC
            """
            
            results = execute_query(sql, tuple(params))
            print(f"Found {len(results)} keyword matches for: {keywords}")
            return results
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def search_recipes_by_category(self, category: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Optimized category search"""
        try:
            category_map = {
                'breakfast': ['breakfast', 'pancake', 'eggs', 'omelette', 'cereal'],
                'lunch': ['lunch', 'sandwich', 'salad', 'soup'],
                'dinner': ['dinner', 'pasta', 'chicken', 'beef', 'fish', 'main'],
                'dessert': ['dessert', 'cake', 'cookie', 'chocolate', 'sweet'],
                'snack': ['snack', 'appetizer']
            }
            
            patterns = category_map.get(category.lower(), [category])
            
            # Use OR for any pattern match
            conditions = []
            params = []
            for pattern in patterns:
                conditions.append("(r.Title LIKE ? OR r.Description LIKE ?)")
                params.extend([f"%{pattern}%", f"%{pattern}%"])
            
            sql = f"""
            SELECT TOP {limit}
                r.RecipeID, r.Title, r.Description, r.Ingredients,
                r.Instructions, r.RawIngredients, r.Servings,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE {' OR '.join(conditions)}
            ORDER BY LikesCount DESC
            """
            
            return execute_query(sql, tuple(params))
            
        except Exception as e:
            print(f"Error searching category: {e}")
            return []
    
    def get_popular_recipes(self, limit: int = 2) -> List[Dict[str, Any]]:
        """Get most liked recipes"""
        try:
            sql = f"""
            SELECT TOP {limit}
                r.RecipeID, r.Title, r.Description, r.Ingredients,
                r.Instructions, r.RawIngredients, r.Servings,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            ORDER BY (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) DESC
            """
            return execute_query(sql)
        except Exception as e:
            print(f"Error getting popular recipes: {e}")
            return []
    
    def _extract_smart_keywords(self, query: str) -> List[str]:
        """Extract relevant cooking keywords"""
        query_lower = query.lower().strip()
        
        # Handle compound cooking terms first
        compound_terms = {
            'mashed potatoes': ['mashed', 'potatoes'],
            'chicken breast': ['chicken', 'breast'], 
            'ice cream': ['ice', 'cream'],
            'olive oil': ['olive', 'oil'],
            'baking powder': ['baking', 'powder'],
            'vanilla extract': ['vanilla', 'extract']
        }
        
        # Check for exact compound matches
        for compound, keywords in compound_terms.items():
            if compound in query_lower:
                return [compound]  # Return compound as single term
        
        # Extract individual meaningful words
        stop_words = {
            'recipe', 'recipes', 'want', 'need', 'looking', 'find', 'show', 'give',
            'new', 'another', 'different', 'make', 'cook', 'prepare', 'i', 'me',
            'can', 'you', 'for', 'a', 'an', 'the', 'and', 'or', 'how', 'what'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)  # Min 3 chars
        keywords = [word for word in words if word not in stop_words]
        
        return keywords[:3]  # Max 3 keywords
    
    def format_recipes_for_prompt(self, recipes: List[Dict[str, Any]]) -> str:
        """Format recipes concisely for AI prompt"""
        if not recipes:
            return "No relevant recipes found in the database."
        
        formatted = []
        for recipe in recipes:
            # Truncate long fields to keep prompt short
            title = recipe.get('Title', 'Untitled')
            author = recipe.get('AuthorName', 'Unknown')
            description = recipe.get('Description', '')[:80] + ('...' if len(recipe.get('Description', '')) > 80 else '')
            ingredients = recipe.get('Ingredients', '')[:120] + ('...' if len(recipe.get('Ingredients', '')) > 120 else '')
            
            recipe_text = f"Recipe: {title}\nBy: {author}\nDescription: {description}\nIngredients: {ingredients}"
            formatted.append(recipe_text)
        
        return "\n\n".join(formatted)
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze what user wants"""
        query_lower = query.lower()
        
        intent = {
            'type': 'general',
            'category': None,
            'specific_request': None
        }
        
        # Check for meal categories
        categories = ['breakfast', 'lunch', 'dinner', 'dessert', 'snack']
        for category in categories:
            if category in query_lower:
                intent['type'] = 'category'
                intent['category'] = category
                break
        
        # Check for specific requests
        if any(word in query_lower for word in ['popular', 'best', 'top']):
            intent['specific_request'] = 'popular'
        elif any(word in query_lower for word in ['new', 'another', 'different']):
            intent['specific_request'] = 'alternative'
        
        return intent