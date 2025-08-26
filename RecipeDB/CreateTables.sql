from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyodbc
import time
import requests
from urllib.parse import quote_plus
import html
import re
from typing import Optional, Tuple, List
from difflib import SequenceMatcher

class RecipeImageScraper:
    def __init__(self, chrome_driver_path: str, connection_string: str):
        self.connection_string = connection_string
        self.chrome_driver_path = chrome_driver_path
        self.driver = None
        self.conn = None
        self.cursor = None
        
        # Track used images to avoid duplicates
        self.used_images = set()
        
        # Statistics
        self.found_images = []
        self.not_found_recipes = []
        self.errors = []
        
    def setup_database(self):
        """Initialize database connection"""
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            print("Database connection established")
            
            # Load already used image URLs - Fixed SQL Server syntax
            self.cursor.execute("SELECT ImageURL FROM Recipes WHERE ImageURL IS NOT NULL AND ImageURL != ''")
            existing_urls = self.cursor.fetchall()
            self.used_images = {url[0] for url in existing_urls if url[0]}
            print(f"Found {len(self.used_images)} existing image URLs")
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise
    
    def setup_selenium(self):
        """Initialize Selenium WebDriver"""
        try:
            options = Options()
            # Uncomment next line for headless mode
            # options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(self.chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            print("Selenium WebDriver initialized")
        except Exception as e:
            print(f"Selenium setup failed: {e}")
            raise
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
    
    def clean_recipe_title(self, title: str) -> str:
        """Clean recipe title for search"""
        title = html.unescape(title)
        title = re.sub(r'[^\w\s-]', ' ', title)
        title = ' '.join(title.split())
        return title.strip()
    
    def validate_image_url(self, url: str) -> bool:
        """Check if image URL is valid and not already used"""
        if not url or url in self.used_images:
            return False
        try:
            response = requests.head(url, timeout=5)
            is_valid = (response.status_code == 200 and 
                       'image' in response.headers.get('content-type', '').lower())
            return is_valid
        except:
            return False
    
    def find_best_matching_recipe(self, target_title: str, recipe_cards) -> Optional[str]:
        """Find the recipe card that best matches our target title"""
        best_match = None
        best_score = 0.3  # Minimum similarity threshold
        
        target_clean = self.clean_recipe_title(target_title).lower()
        
        for card in recipe_cards:
            try:
                # Try to get recipe title from the card
                title_elem = card.find_element(By.CSS_SELECTOR, "a[title], h3, h2, .recipe-title, .title")
                card_title = title_elem.get_attribute("title") or title_elem.text
                
                if not card_title:
                    continue
                    
                card_title_clean = self.clean_recipe_title(card_title).lower()
                
                # Calculate similarity
                score = self.similarity(target_clean, card_title_clean)
                
                print(f"  Comparing '{target_title}' with '{card_title}' - Score: {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_match = card
                    
            except Exception as e:
                continue
        
        if best_match:
            print(f"  Best match found with score: {best_score:.2f}")
        
        return best_match
    
    def get_recipe_image_from_card(self, card) -> Optional[str]:
        """Extract image URL from a recipe card"""
        image_selectors = [
            "img[src*='recipe']",
            "img[data-src*='recipe']",
            "img.recipe-image",
            "img.card-image", 
            "img",
            ".image img",
            ".photo img"
        ]
        
        for selector in image_selectors:
            try:
                img_elem = card.find_element(By.CSS_SELECTOR, selector)
                img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
                
                if img_url and self.validate_image_url(img_url):
                    return img_url
            except:
                continue
        
        return None
    
    def search_recipe_on_food_com(self, title: str) -> Optional[str]:
        """Search for recipe on food.com and return image URL"""
        clean_title = self.clean_recipe_title(title)
        search_url = f"https://www.food.com/search/{quote_plus(clean_title)}"
        
        try:
            print(f"Searching for: {title}")
            print(f"URL: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)  # Let page load completely
            
            # Look for recipe cards on search results page
            card_selectors = [
                ".recipe-card",
                ".search-result", 
                ".card",
                "[data-testid*='recipe']",
                ".recipe-summary"
            ]
            
            recipe_cards = []
            for selector in card_selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        recipe_cards.extend(cards)
                        print(f"  Found {len(cards)} cards with selector: {selector}")
                except:
                    continue
            
            if not recipe_cards:
                print("  No recipe cards found on search page")
                return None
            
            # Find best matching recipe card
            best_card = self.find_best_matching_recipe(title, recipe_cards)
            
            if not best_card:
                print("  No good match found among recipe cards")
                return None
            
            # Try to get image from the card first
            image_url = self.get_recipe_image_from_card(best_card)
            if image_url:
                print(f"  Found image from card: {image_url}")
                self.used_images.add(image_url)
                return image_url
            
            # If no image in card, try to go to the recipe page
            try:
                recipe_link = best_card.find_element(By.CSS_SELECTOR, "a")
                recipe_url = recipe_link.get_attribute("href")
                
                if recipe_url:
                    print(f"  Going to recipe page: {recipe_url}")
                    self.driver.get(recipe_url)
                    time.sleep(2)
                    
                    # Look for main recipe image
                    main_img_selectors = [
                        ".recipe-image img",
                        ".hero-image img",
                        ".main-image img",
                        "[class*='primary'] img",
                        ".recipe-photo img"
                    ]
                    
                    for selector in main_img_selectors:
                        try:
                            img_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            img_url = img_elem.get_attribute("src")
                            
                            if img_url and self.validate_image_url(img_url):
                                print(f"  Found image from recipe page: {img_url}")
                                self.used_images.add(img_url)
                                return img_url
                        except:
                            continue
            except:
                pass
            
            print("  No valid image found")
            return None
            
        except Exception as e:
            print(f"  Error searching for {title}: {e}")
            return None
    
    def update_recipe_image(self, title: str, image_url: str) -> bool:
        """Update recipe image URL in database"""
        try:
            self.cursor.execute(
                "UPDATE Recipes SET ImageURL = ? WHERE Title = ?", 
                (image_url, title)
            )
            affected_rows = self.cursor.rowcount
            self.conn.commit()
            
            if affected_rows > 0:
                return True
            else:
                print(f"  Warning: No rows updated for title '{title}'")
                return False
        except Exception as e:
            print(f"  Database update error for {title}: {e}")
            return False
    
    def get_recipes_without_images(self, limit: Optional[int] = None) -> List[str]:
        """Get recipes without images - Fixed for SQL Server"""
        try:
            if limit:
                query = f"SELECT TOP {limit} Title FROM Recipes WHERE ImageURL IS NULL OR ImageURL = '' ORDER BY RecipeID"
            else:
                query = "SELECT Title FROM Recipes WHERE ImageURL IS NULL OR ImageURL = '' ORDER BY RecipeID"
            
            self.cursor.execute(query)
            recipes = [row[0] for row in self.cursor.fetchall()]
            print(f"Database query returned {len(recipes)} recipes without images")
            return recipes
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
                image_url = self.search_recipe_on_food_com(title)
                
                if image_url:
                    if self.update_recipe_image(title, image_url):
                        self.found_images.append((title, image_url))
                        print(f"  SUCCESS: Updated image for '{title}'")
                    else:
                        self.errors.append((title, "Database update failed"))
                else:
                    self.not_found_recipes.append(title)
                    print(f"  FAILED: No image found for '{title}'")
                
                # Delay between requests
                time.sleep(3)
                
            except Exception as e:
                error_msg = f"Processing error: {e}"
                self.errors.append((title, error_msg))
                print(f"  ERROR: {error_msg}")
    
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
            for title, url in self.found_images:
                print(f"  - {title}")
                print(f"    {url}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.conn:
            self.conn.close()
    
    def run(self, limit: Optional[int] = None):
        """Run the complete scraping process"""
        try:
            self.setup_database()
            self.setup_selenium()
            self.process_recipes(limit)
            self.print_summary()
        except Exception as e:
            print(f"Critical error: {e}")
        finally:
            self.cleanup()


def main():
    CHROME_DRIVER_PATH = r"C:\Users\User\Downloads\ShareBite\ShareBite\RecipeDB\chromedriver-win64\chromedriver.exe"
    CONNECTION_STRING = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=RecipeDB.mssql.somee.com;"
        "DATABASE=RecipeDB;"
        "UID=ShiraAlk_SQLLogin_1;"
        "PWD=6nX2uN7f;"
        "TrustServerCertificate=yes;"
        "Encrypt=yes;"
    )
    
    scraper = RecipeImageScraper(CHROME_DRIVER_PATH, CONNECTION_STRING)
    
    # Test with just 3 recipes first
    scraper.run(limit=3)


if __name__ == "__main__":
    main()