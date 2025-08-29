import requests
import pyodbc
from urllib.parse import quote_plus
import html
import re
import json
from typing import Optional, List
import time

class AlternativeRecipeScraper:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
        
        # Statistics
        self.found_images = []
        self.not_found_recipes = []
        self.errors = []
        
        # Session with headers to look like a real browser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def setup_database(self):
        """Initialize database connection"""
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            print("Database connection established")
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise
    
    def clean_recipe_title(self, title: str) -> str:
        """Clean recipe title for search"""
        title = html.unescape(title)
        title = re.sub(r'[^\w\s&-]', ' ', title)
        title = ' '.join(title.split())
        return title.strip()
    
    def search_recipe_image_api(self, recipe_title: str) -> Optional[str]:
        """
        Search for recipe images using only FOOD-RELATED free sources
        """
        clean_title = self.clean_recipe_title(recipe_title)
        
        # Method 1: Foodish API (completely free, actual food images)
        try:
            print(f"Searching Foodish API for random food image")
            foodish_url = "https://foodish-api.herokuapp.com/api/"
            
            response = self.session.get(foodish_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('image'):
                    image_url = data['image']
                    print(f"Found Foodish image: {image_url}")
                    return image_url
                    
        except Exception as e:
            print(f"Foodish API search failed: {e}")
        
        # Method 2: TheMealDB (free, no API key needed)
        try:
            print(f"Searching TheMealDB for: {clean_title}")
            meal_url = f"https://www.themealdb.com/api/v1/1/search.php?s={quote_plus(clean_title)}"
            
            response = self.session.get(meal_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('meals') and len(data['meals']) > 0:
                    image_url = data['meals'][0].get('strMealThumb')
                    if image_url:
                        print(f"Found TheMealDB image: {image_url}")
                        return image_url
                        
        except Exception as e:
            print(f"TheMealDB search failed: {e}")
        
        # Method 3: Try ingredient-based search on TheMealDB
        try:
            keywords = clean_title.lower().split()
            food_words = ['chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'chocolate', 
                         'vanilla', 'strawberry', 'apple', 'banana', 'rice', 'pasta', 
                         'bread', 'cake', 'cookies', 'pie', 'soup', 'salad', 'garlic',
                         'pepper', 'shrimp', 'cheese', 'burger', 'biscuit', 'pizza', 'stir', 'fry']
            
            for word in keywords:
                if word in food_words:
                    print(f"Searching TheMealDB by ingredient: {word}")
                    ingredient_url = f"https://www.themealdb.com/api/v1/1/filter.php?i={word}"
                    
                    response = self.session.get(ingredient_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            # Get a random meal from the results instead of always the first
                            import random
                            random_meal = random.choice(data['meals'][:5])  # Pick from first 5
                            image_url = random_meal.get('strMealThumb')
                            if image_url:
                                print(f"Found ingredient-based image for {word}: {image_url}")
                                return image_url
                        
        except Exception as e:
            print(f"Ingredient search failed: {e}")
        
        # Method 4: Recipe Puppy API (free, no key needed)
        try:
            print(f"Searching Recipe Puppy for: {clean_title}")
            puppy_url = f"http://www.recipepuppy.com/api/?q={quote_plus(clean_title)}"
            
            response = self.session.get(puppy_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    for result in data['results'][:5]:
                        if result.get('thumbnail') and result['thumbnail'].strip():
                            image_url = result['thumbnail']
                            if self.validate_image_url(image_url):
                                print(f"Found Recipe Puppy image: {image_url}")
                                return image_url
                        
        except Exception as e:
            print(f"Recipe Puppy search failed: {e}")
        
        # Method 5: Comprehensive food fallback mapping (curated food images)
        try:
            print(f"Using food-specific fallbacks for: {clean_title}")
            
            food_fallbacks = {
                'lamb': 'https://www.themealdb.com/images/media/meals/sytuqu1511553755.jpg',
                'garlic': 'https://www.themealdb.com/images/media/meals/qrqywr1503066729.jpg',
                'pepper': 'https://www.themealdb.com/images/media/meals/qrqywr1503066729.jpg',
                'chocolate': 'https://www.themealdb.com/images/media/meals/xqvusu1511814580.jpg',
                'biscuits': 'https://www.themealdb.com/images/media/meals/1550441275.jpg',
                'biscuit': 'https://www.themealdb.com/images/media/meals/1550441275.jpg',
                'pizza': 'https://www.themealdb.com/images/media/meals/x0lk931587671540.jpg',
                'shrimp': 'https://www.themealdb.com/images/media/meals/1550441882.jpg',
                'stir': 'https://www.themealdb.com/images/media/meals/1548772327.jpg',  # stir fry
                'burger': 'https://www.themealdb.com/images/media/meals/k420tj1585565244.jpg',
                'chicken': 'https://www.themealdb.com/images/media/meals/wyxwsp1486979827.jpg',
                'beef': 'https://www.themealdb.com/images/media/meals/qtqvys1468573168.jpg',
                'pork': 'https://www.themealdb.com/images/media/meals/rlwcc51598734603.jpg',
                'fish': 'https://www.themealdb.com/images/media/meals/1548772327.jpg',
                'cake': 'https://www.themealdb.com/images/media/meals/adxcbq1619787919.jpg',
                'soup': 'https://www.themealdb.com/images/media/meals/58oia61564916529.jpg',
                'pasta': 'https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg',
                'salad': 'https://www.themealdb.com/images/media/meals/rqtxvr1511792990.jpg',
                'cheese': 'https://www.themealdb.com/images/media/meals/k420tj1585565244.jpg'  # cheese burger
            }
            
            title_lower = clean_title.lower()
            for food_type, image_url in food_fallbacks.items():
                if food_type in title_lower:
                    print(f"Found fallback food image for {food_type}")
                    return image_url
                    
        except Exception as e:
            print(f"Fallback images search failed: {e}")
        
        # Method 6: Category-based food images from TheMealDB
        try:
            print(f"Trying category-based food images")
            
            # Map recipe types to TheMealDB categories
            category_mapping = {
                'lamb': 'Lamb',
                'beef': 'Beef', 
                'chicken': 'Chicken',
                'pork': 'Pork',
                'fish': 'Seafood',
                'shrimp': 'Seafood',
                'pasta': 'Pasta',
                'dessert': 'Dessert',
                'cake': 'Dessert',
                'chocolate': 'Dessert'
            }
            
            title_lower = clean_title.lower()
            for keyword, category in category_mapping.items():
                if keyword in title_lower:
                    print(f"Searching TheMealDB category: {category}")
                    category_url = f"https://www.themealdb.com/api/v1/1/filter.php?c={category}"
                    
                    response = self.session.get(category_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            import random
                            random_meal = random.choice(data['meals'][:10])
                            image_url = random_meal.get('strMealThumb')
                            if image_url:
                                print(f"Found category image for {category}")
                                return image_url
                            
        except Exception as e:
            print(f"Category search failed: {e}")
        
        # Method 7: Use a default generic food image as absolute last resort
        try:
            print(f"Using generic food images as last resort")
            generic_food_images = [
                "https://www.themealdb.com/images/media/meals/llcbn01574687627.jpg",
                "https://www.themealdb.com/images/media/meals/ustsqw1468250014.jpg", 
                "https://www.themealdb.com/images/media/meals/urzj1d1587670465.jpg"
            ]
            
            import random
            selected_image = random.choice(generic_food_images)
            if self.validate_image_url(selected_image):
                print(f"Using generic food image: {selected_image}")
                return selected_image
                    
        except Exception as e:
            print(f"Generic food images failed: {e}")
        
        print(f"No food images found for: {clean_title}")
        return None
    
    def validate_image_url(self, url: str) -> bool:
        """Check if image URL is accessible"""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def update_recipe_image(self, title: str, image_url: str) -> bool:
        """Update recipe image URL in database"""
        try:
            self.cursor.execute(
                "UPDATE Recipes SET ImageURL = ? WHERE Title = ?", 
                (image_url, title)
            )
            affected_rows = self.cursor.rowcount
            self.conn.commit()
            return affected_rows > 0
        except Exception as e:
            print(f"Database update error for {title}: {e}")
            return False
    
    def get_recipes_without_images(self, limit: Optional[int] = None) -> List[str]:
        """Get recipes without images"""
        try:
            if limit:
                query = f"SELECT TOP {limit} Title FROM Recipes WHERE ImageURL IS NULL OR ImageURL = '' ORDER BY RecipeID"
            else:
                query = "SELECT Title FROM Recipes WHERE ImageURL IS NULL OR ImageURL = '' ORDER BY RecipeID"
            
            self.cursor.execute(query)
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching recipes: {e}")
            return []
    
    def process_recipes(self, limit: Optional[int] = None):
        """Main processing function"""
        recipes = self.get_recipes_without_images(limit)
        
        total_recipes = len(recipes)
        print(f"Found {total_recipes} recipes without images")
        
        if total_recipes == 0:
            print("All recipes already have images!")
            return
        
        for i, title in enumerate(recipes, 1):
            print(f"\n[{i}/{total_recipes}] Processing: {title}")
            
            try:
                image_url = self.search_recipe_image_api(title)
                
                if image_url and self.validate_image_url(image_url):
                    if self.update_recipe_image(title, image_url):
                        self.found_images.append((title, image_url))
                        print(f"SUCCESS: Updated image for '{title}'")
                    else:
                        self.errors.append((title, "Database update failed"))
                else:
                    self.not_found_recipes.append(title)
                    print(f"FAILED: No image found for '{title}'")
                
                # Delay between requests
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"Processing error: {e}"
                self.errors.append((title, error_msg))
                print(f"ERROR: {error_msg}")
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        
        print(f"Successfully updated: {len(self.found_images)} recipes")
        print(f"Images not found: {len(self.not_found_recipes)} recipes")
        print(f"Errors occurred: {len(self.errors)} recipes")
        
        if self.found_images:
            print(f"\nSuccessfully found images:")
            for title, url in self.found_images[:5]:  # Show first 5
                print(f"  - {title}")
                print(f"    {url}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()
    
    def run(self, limit: Optional[int] = None):
        """Run the complete scraping process"""
        try:
            self.setup_database()
            self.process_recipes(limit)
            self.print_summary()
        except Exception as e:
            print(f"Critical error: {e}")
        finally:
            self.cleanup()


def main():
    CONNECTION_STRING = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=RecipeDB.mssql.somee.com;"
        "DATABASE=RecipeDB;"
        "UID=ShiraAlk_SQLLogin_1;"
        "PWD=6nX2uN7f;"
        "TrustServerCertificate=yes;"
        "Encrypt=yes;"
    )
    
    scraper = AlternativeRecipeScraper(CONNECTION_STRING)
    scraper.run()


if __name__ == "__main__":
    main()