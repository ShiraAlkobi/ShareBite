import pyodbc
import pandas as pd
import ast
import random
from datetime import datetime, timedelta
import hashlib

# SOMEE database connection details
# Update these with your actual credentials
SERVER = 'RecipeDB.mssql.somee.com'  # Replace with your server name
DATABASE = 'RecipeDB'  # Replace with your database name
USERNAME = 'ShiraAlk_SQLLogin_1'  # Replace with your username
PASSWORD = '6nX2uN7f'  # Replace with your password

# Connection string
connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;Encrypt=yes;"
def create_password_hash(password):
    """Create password hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_users(cursor):
    """Create 10 new users"""
    users_data = [
        ('chef_master', 'chef.master@gmail.com', 'Passionate home chef who loves experimenting with flavors'),
        ('kitchen_guru', 'kitchen.guru@gmail.com', 'Cooking enthusiast sharing family recipes'),
        ('foodie_mom', 'foodie.mom@gmail.com', 'Mom of three who loves creating healthy meals'),
        ('spice_wizard', 'spice.wizard@gmail.com', 'Expert in international cuisines and spices'),
        ('healthy_cook', 'healthy.cook@gmail.com', 'Focused on nutritious and delicious meals'),
        ('quick_chef', 'quick.chef@gmail.com', 'Specializing in fast and easy recipes'),
        ('gourmet_lover', 'gourmet.lover@gmail.com', 'Fine dining recipes for home cooking'),
        ('veggie_master', 'veggie.master@gmail.com', 'Plant-based cooking enthusiast'),
        ('comfort_cook', 'comfort.cook@gmail.com', 'Traditional comfort food specialist'),
        ('creative_baker', 'creative.baker@gmail.com', 'Love baking and creative desserts')
    ]
    
    created_users = []
    for i, (username, email, bio) in enumerate(users_data):
        password_hash = create_password_hash(f"password{i+1}")
        
        try:
            cursor.execute("""
                INSERT INTO Users (Username, Email, PasswordHash, Bio)
                VALUES (?, ?, ?, ?)
            """, username, email, password_hash, bio)
            
            # Get the created UserID
            cursor.execute("SELECT @@IDENTITY")
            user_id = cursor.fetchone()[0]
            created_users.append(user_id)
            print(f"Created user: {username} with ID: {user_id}")
            
        except Exception as e:
            print(f"Error creating user {username}: {e}")
    
    return created_users

def get_or_create_tag(cursor, tag_name):
    """Get or create tag"""
    # Check if tag already exists
    cursor.execute("SELECT TagID FROM Tags WHERE TagName = ?", tag_name)
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        # Create new tag
        cursor.execute("INSERT INTO Tags (TagName) VALUES (?)", tag_name)
        cursor.execute("SELECT @@IDENTITY")
        return cursor.fetchone()[0]

def random_date_between(start_date, end_date):
    """Generate random date between two dates"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def process_recipes(cursor, csv_file_path, user_ids):
    """Process and insert recipes"""
    # Read the CSV file
    df = pd.read_csv(csv_file_path, encoding='latin-1')
    
    # Limit to the first 100 records
    df = df.head(100)
    
    # Dates for random selection
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 9, 1)
    
    recipe_count = 0
    for index, row in df.iterrows():
        try:
            # Select a random user (every 10 recipes per user)
            author_id = user_ids[recipe_count // 10]
            
            # Process the data
            title = row['name']
            description = row['description']
            raw_ingredients = row['ingredients']
            ingredients = row['ingredients_raw_str']
            servings = int(row['servings']) if pd.notna(row['servings']) else None
            instructions = str(row['steps']) if pd.notna(row['steps']) else ''
            created_at = random_date_between(start_date, end_date)
            
            # Insert the recipe
            cursor.execute("""
                INSERT INTO Recipes (AuthorID, Title, Description, Ingredients, Instructions, 
                                   RawIngredients, Servings, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, author_id, title, description, ingredients, instructions, 
                raw_ingredients, servings, created_at)
            
            # Get the created RecipeID
            cursor.execute("SELECT @@IDENTITY")
            recipe_id = cursor.fetchone()[0]
            
            # Process tags
            search_terms = row['search_terms']
            if pd.notna(search_terms):
                try:
                    # Convert from string to set
                    tags_set = ast.literal_eval(search_terms)
                    
                    for tag_name in tags_set:
                        tag_name = str(tag_name).strip()
                        if tag_name:
                            # Get or create the tag
                            tag_id = get_or_create_tag(cursor, tag_name)
                            
                            # Create the relation between recipe and tag
                            cursor.execute("""
                                INSERT INTO RecipeTags (RecipeID, TagID)
                                VALUES (?, ?)
                            """, recipe_id, tag_id)
                
                except Exception as e:
                    print(f"Error processing tags for recipe {title}: {e}")
            
            recipe_count += 1
            print(f"Inserted recipe {recipe_count}: {title} (Author ID: {author_id})")
            
        except Exception as e:
            print(f"Error inserting recipe {row['name']}: {e}")
            continue

def main():
    """Main function"""
    try:
        # Connect to the database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print("Successfully connected to the database!")
        
        # Create 10 users
        print("\n=== Creating users ===")
        user_ids = create_users(cursor)
        conn.commit()
        
        if len(user_ids) != 10:
            print(f"Only {len(user_ids)} users were created instead of 10")
            return
        
        # Process recipes
        print("\n=== Processing recipes ===")
        csv_file_path = r"C:\\Users\\shira\\OneDrive\\שולחן העבודה\\ShareBite\\ShareBite\\RecipeDB\\recipes_w_search_terms.csv"
        process_recipes(cursor, csv_file_path, user_ids)
        
        # Save changes
        conn.commit()
        print("\n=== Completed successfully! ===")
        print("10 users and 100 recipes with tags were created")
        
    except FileNotFoundError:
        print(f"File not found: {csv_file_path}")
        print("Make sure the path is correct")
        
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        print("Make sure the connection details are correct")
        
    except Exception as e:
        print(f"General error: {e}")
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("Connection closed")

if __name__ == "__main__":
    # Installation instructions
    print("Before running the script, make sure you have installed:")
    print("pip install pyodbc pandas")
    print("And that you have ODBC Driver 17 for SQL Server installed")
    print("\nUpdate the connection details at the top of the file!")
    print("=" * 50)
    
    main()