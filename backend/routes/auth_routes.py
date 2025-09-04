from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
import os
import hashlib
import json

# Import database functions directly
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# ============= EVENT SOURCING HELPER =============
def log_user_event(user_id: int, action_type: str, event_data: Dict = None):
    """
    Log a user event to the RecipeEvents table for event sourcing
    Note: We use recipe_id = 0 for user-related events since it's not recipe-specific
    
    Args:
        user_id (int): ID of the user performing the action
        action_type (str): Type of action (UserRegistered, UserLoggedIn, UserLoggedOut, etc.)
        event_data (Dict): Additional data to store as JSON
    """
    try:
        # Convert event_data to JSON string if provided
        event_data_json = json.dumps(event_data) if event_data else None
        
        # Insert event into RecipeEvents table (using RecipeID = 0 for user events)
        execute_non_query(
            """INSERT INTO RecipeEvents (RecipeID, UserID, ActionType, EventData) 
               VALUES (?, ?, ?, ?)""",
            (0, user_id, action_type, event_data_json)
        )
        
        print(f"🔍 User event logged: {action_type} - User {user_id}")
        
    except Exception as e:
        print(f"⚠️ Failed to log user event: {e}")
        # Don't raise exception - event logging failure shouldn't break the main operation

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    bio: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    userid: int
    username: str
    email: str
    profilepicurl: Optional[str] = None
    bio: Optional[str] = None
    createdat: datetime

def create_password_hash(password: str) -> str:
    """Create password hash using SHA256"""
    if not isinstance(password, str):
        print(f"⚠️ Warning: Password is not a string, type: {type(password)}")
        password = str(password)
    
    hash_result = hashlib.sha256(password.encode()).hexdigest()
    print(f"🔒 Hash function: input='{password}' -> output='{hash_result[:20]}...'")
    return hash_result

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    # המר את sub למחרוזת אם הוא מספר
    if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
        to_encode['sub'] = str(to_encode['sub'])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username from database"""
    try:
        print(f"🔍 Searching for user: '{username}'")
        result = execute_query(
            "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE Username = ?", 
            (username,), 
            fetch="one"
        )
        
        print(f"🔍 Raw database result: {result}")
        print(f"🔍 Result type: {type(result)}")
        
        if result and len(result) > 0:
            # Your execute_query returns a list of dictionaries
            if isinstance(result, list) and len(result) > 0:
                row = result[0]  # Get first result
                
                # Check if it's a dictionary (your format) or tuple
                if isinstance(row, dict):
                    print(f"🔍 Processing dictionary row: {dict(row, PasswordHash='***HIDDEN***')}")
                    
                    user_dict = {
                        'userid': int(row['UserID']),
                        'username': str(row['Username']) if row['Username'] else None,
                        'email': str(row['Email']) if row['Email'] else None,
                        'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                        'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                        'bio': str(row['Bio']) if row['Bio'] else None,
                        'createdat': row['CreatedAt']
                    }
                else:
                    # Handle tuple format (if your DB returns tuples)
                    print(f"🔍 Processing tuple row: {row}")
                    user_dict = {
                        'userid': int(row[0]),
                        'username': str(row[1]) if row[1] else None,
                        'email': str(row[2]) if row[2] else None,
                        'passwordhash': str(row[3]) if row[3] else None,
                        'profilepicurl': str(row[4]) if row[4] else None,
                        'bio': str(row[5]) if row[5] else None,
                        'createdat': row[6]
                    }
                
                print(f"🔍 Created user dict: {dict(user_dict, passwordhash='***HIDDEN***')}")
                return user_dict
            
        print(f"🔍 No user found with username: '{username}'")
        return None
        
    except Exception as e:
        print(f"❌ Error getting user by username: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email from database"""
    try:
        result = execute_query(
            "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE Email = ?", 
            (email,), 
            fetch="one"
        )
        
        if result and len(result) > 0:
            row = result[0]  # Get first result
            
            if isinstance(row, dict):
                return {
                    'userid': int(row['UserID']),
                    'username': str(row['Username']) if row['Username'] else None,
                    'email': str(row['Email']) if row['Email'] else None,
                    'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                    'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                    'bio': str(row['Bio']) if row['Bio'] else None,
                    'createdat': row['CreatedAt']
                }
            else:
                # Handle tuple format
                return {
                    'userid': int(row[0]),
                    'username': str(row[1]) if row[1] else None,
                    'email': str(row[2]) if row[2] else None,
                    'passwordhash': str(row[3]) if row[3] else None,
                    'profilepicurl': str(row[4]) if row[4] else None,
                    'bio': str(row[5]) if row[5] else None,
                    'createdat': row[6]
                }
        return None
        
    except Exception as e:
        print(f"❌ Error getting user by email: {e}")
        return None

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID from database"""
    try:
        result = execute_query(
            "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE UserID = ?", 
            (user_id,), 
            fetch="one"
        )
        
        if result and len(result) > 0:
            row = result[0]  # Get first result
            
            if isinstance(row, dict):
                return {
                    'userid': int(row['UserID']),
                    'username': str(row['Username']) if row['Username'] else None,
                    'email': str(row['Email']) if row['Email'] else None,
                    'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                    'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                    'bio': str(row['Bio']) if row['Bio'] else None,
                    'createdat': row['CreatedAt']
                }
            else:
                # Handle tuple format
                return {
                    'userid': int(row[0]),
                    'username': str(row[1]) if row[1] else None,
                    'email': str(row[2]) if row[2] else None,
                    'passwordhash': str(row[3]) if row[3] else None,
                    'profilepicurl': str(row[4]) if row[4] else None,
                    'bio': str(row[5]) if row[5] else None,
                    'createdat': row[6]
                }
        return None
        
    except Exception as e:
        print(f"❌ Error getting user by ID: {e}")
        return None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        
        # קבל את sub כמחרוזת והמר למספר
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # המר למספר
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        print(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return access token - LOGS UserLoggedIn EVENT
    """
    try:
        print(f"🔍 Login attempt for username: {login_data.username}")
        
        # Get user by username
        user = get_user_by_username(login_data.username)
        if not user:
            print(f"❌ User not found: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        print(f"✅ User found: {user['username']}")
        print(f"🔍 Stored password hash: {user['passwordhash'][:20]}...")
        
        # Verify password
        password_hash = create_password_hash(login_data.password)
        print(f"🔍 Calculated password hash: {password_hash[:20]}...")
        print(f"🔍 Password hashes match: {user['passwordhash'] == password_hash}")
        
        if user['passwordhash'] != password_hash:
            print(f"❌ Invalid password for user: {login_data.username}")
            print(f"❌ Expected: {user['passwordhash']}")
            print(f"❌ Got: {password_hash}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": int(user['userid'])}, expires_delta=access_token_expires
        )
        
        # Log user login event
        login_event_data = {
            "username": user['username'],
            "email": user['email'],
            "login_timestamp": datetime.now().isoformat(),
            "token_expires_at": (datetime.now() + access_token_expires).isoformat(),
            "login_method": "username_password"
        }
        log_user_event(user['userid'], "UserLoggedIn", login_event_data)
        
        # Prepare user data for response (exclude password hash)
        user_data = {
            "userid": int(user['userid']),
            "username": str(user['username']),
            "email": str(user['email']),
            "profilepicurl": user['profilepicurl'],
            "bio": user['bio'],
            "createdat": user['createdat']
        }
        
        print(f"✅ Login successful for user: {login_data.username}")
        
        return AuthResponse(
            access_token=access_token,
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/register", response_model=AuthResponse)
async def register(register_data: RegisterRequest):
    """
    Register new user - LOGS UserRegistered EVENT
    """
    try:
        print(f"🔍 Registration attempt for username: {register_data.username}")
        print(f"🔍 Registration email: {register_data.email}")
        
        # Check if username already exists
        print(f"🔍 Checking if username exists: {register_data.username}")
        existing_user = get_user_by_username(register_data.username)
        if existing_user:
            print(f"❌ Username already exists: {register_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        print(f"🔍 Checking if email exists: {register_data.email}")
        existing_email = get_user_by_email(register_data.email)
        if existing_email:
            print(f"❌ Email already exists: {register_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create password hash
        print(f"🔍 Creating password hash for password: {'*' * len(register_data.password)}")
        password_hash = create_password_hash(register_data.password)
        print(f"🔍 Generated password hash: {password_hash}")
        print(f"🔍 Password hash length: {len(password_hash)}")
        
        # Clean bio field - handle None and empty strings
        bio_value = None
        if register_data.bio and register_data.bio.strip():
            bio_value = register_data.bio.strip()
        
        print(f"💾 Bio value: {bio_value}")
        print(f"💾 About to insert - Username: {register_data.username}, Email: {register_data.email}")
        
        # Insert new user
        print(f"💾 Creating user in database...")
        try:
            # Log the exact values being inserted
            insert_values = (register_data.username, register_data.email, password_hash, None, bio_value)
            print(f"💾 Insert values: {[str(v) if v is not None else None for v in insert_values]}")
            print(f"💾 Insert value types: {[type(v) for v in insert_values]}")
            
            user_id = insert_and_get_id(
                "Users",
                ["Username", "Email", "PasswordHash", "ProfilePicURL", "Bio"],
                insert_values
            )
            print(f"💾 Raw user_id from database: {user_id} (type: {type(user_id)})")
            
            if not user_id:
                print(f"❌ Failed to create user in database")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            # Convert user_id to int if it's a Decimal
            if hasattr(user_id, '__int__'):
                user_id = int(user_id)
            print(f"✅ User created with ID: {user_id} (type: {type(user_id)})")
            
            # VERIFICATION: Immediately test if we can retrieve the user and verify password
            print(f"🔍 VERIFICATION: Testing immediate password verification...")
            test_user = get_user_by_username(register_data.username)
            if test_user:
                test_hash = create_password_hash(register_data.password)
                verification_result = test_user['passwordhash'] == test_hash
                print(f"🔍 VERIFICATION: User retrieved: ✅")
                print(f"🔍 VERIFICATION: Stored hash: {test_user['passwordhash']}")
                print(f"🔍 VERIFICATION: Test hash: {test_hash}")
                print(f"🔍 VERIFICATION: Hashes match: {verification_result}")
                if not verification_result:
                    print(f"⚠️ WARNING: Password verification failed immediately after registration!")
            else:
                print(f"🔍 VERIFICATION: Could not retrieve user immediately after creation!")
            
        except Exception as db_error:
            print(f"❌ Database insertion error: {db_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        # Log user registration event
        registration_event_data = {
            "username": register_data.username,
            "email": str(register_data.email),
            "has_bio": bio_value is not None,
            "registration_timestamp": datetime.now().isoformat(),
            "registration_method": "direct_signup"
        }
        log_user_event(user_id, "UserRegistered", registration_event_data)
        
        # Create access token
        print(f"🔍 Creating access token for user ID: {user_id}")
        try:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": int(user_id)}, expires_delta=access_token_expires
            )
            print(f"✅ Access token created successfully")
        except Exception as token_error:
            print(f"❌ Token creation error: {token_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token creation error: {str(token_error)}"
            )
        
        # Prepare user data for response
        print(f"📦 Preparing user data response...")
        try:
            user_data = {
                "userid": int(user_id),  # Ensure it's an integer
                "username": str(register_data.username),
                "email": str(register_data.email),
                "profilepicurl": None,
                "bio": bio_value,  # Use cleaned bio value
                "createdat": datetime.now().isoformat()  # Convert to string for JSON serialization
            }
            print(f"📦 User data prepared: {user_data}")
            print(f"📦 User data types: {[(k, type(v)) for k, v in user_data.items()]}")
        except Exception as data_error:
            print(f"❌ User data preparation error: {data_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data preparation error: {str(data_error)}"
            )
        
        print(f"✅ Registration successful for user: {register_data.username}")
        
        # Create response object
        print(f"📡 Creating AuthResponse object...")
        try:
            response = AuthResponse(
                access_token=access_token,
                user=user_data
            )
            print(f"✅ AuthResponse created successfully")
            print(f"📡 About to return response...")
            return response
        except Exception as response_error:
            print(f"❌ Response creation error: {response_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response creation error: {str(response_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """
    Get current authenticated user - READ ONLY (no event logging)
    """
    return UserResponse(
        userid=current_user['userid'],
        username=current_user['username'],
        email=current_user['email'],
        profilepicurl=current_user['profilepicurl'],
        bio=current_user['bio'],
        createdat=current_user['createdat']
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """
    Logout user - LOGS UserLoggedOut EVENT
    """
    try:
        # Log user logout event
        logout_event_data = {
            "username": current_user['username'],
            "logout_timestamp": datetime.now().isoformat(),
            "logout_method": "explicit_logout"
        }
        log_user_event(current_user['userid'], "UserLoggedOut", logout_event_data)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        print(f"❌ Logout error: {e}")
        # Still return success message even if event logging fails
        return {"message": "Successfully logged out"}