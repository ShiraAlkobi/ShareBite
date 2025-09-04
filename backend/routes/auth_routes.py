from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
import os

# Import User model
from models.user import User

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    # Convert sub to string if it's a number
    if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
        to_encode['sub'] = str(to_encode['sub'])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Get sub as string and convert to number
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Convert to number
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = User.get_user_by_id_dict(user_id)
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
        print(f"Login attempt for username: {login_data.username}")
        
        # Get user by username using User model
        user = User.get_by_username(login_data.username)
        if not user:
            print(f"User not found: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        print(f"User found: {user['username']}")
        print(f"Stored password hash: {user['passwordhash'][:20]}...")
        
        # Verify password using User model
        password_hash = User.create_password_hash(login_data.password)
        print(f"Calculated password hash: {password_hash[:20]}...")
        print(f"Password hashes match: {user['passwordhash'] == password_hash}")
        
        if user['passwordhash'] != password_hash:
            print(f"Invalid password for user: {login_data.username}")
            print(f"Expected: {user['passwordhash']}")
            print(f"Got: {password_hash}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": int(user['userid'])}, expires_delta=access_token_expires
        )
        
        # Log user login event using User model
        login_event_data = {
            "username": user['username'],
            "email": user['email'],
            "login_timestamp": datetime.now().isoformat(),
            "token_expires_at": (datetime.now() + access_token_expires).isoformat(),
            "login_method": "username_password"
        }
        User.log_user_event(user['userid'], "UserLoggedIn", login_event_data)
        
        # Prepare user data for response (exclude password hash)
        user_data = {
            "userid": int(user['userid']),
            "username": str(user['username']),
            "email": str(user['email']),
            "profilepicurl": user['profilepicurl'],
            "bio": user['bio'],
            "createdat": user['createdat']
        }
        
        print(f"Login successful for user: {login_data.username}")
        
        return AuthResponse(
            access_token=access_token,
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
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
        print(f"Registration attempt for username: {register_data.username}")
        print(f"Registration email: {register_data.email}")
        
        # Check if username already exists using User model
        print(f"Checking if username exists: {register_data.username}")
        existing_user = User.get_by_username(register_data.username)
        if existing_user:
            print(f"Username already exists: {register_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists using User model
        print(f"Checking if email exists: {register_data.email}")
        existing_email = User.get_by_email(register_data.email)
        if existing_email:
            print(f"Email already exists: {register_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user using User model
        user_id = User.create_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            bio=register_data.bio
        )
        
        if not user_id:
            print(f"Failed to create user in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Log user registration event using User model
        registration_event_data = {
            "username": register_data.username,
            "email": str(register_data.email),
            "has_bio": register_data.bio is not None and register_data.bio.strip() != "",
            "registration_timestamp": datetime.now().isoformat(),
            "registration_method": "direct_signup"
        }
        User.log_user_event(user_id, "UserRegistered", registration_event_data)
        
        # Create access token
        print(f"Creating access token for user ID: {user_id}")
        try:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": int(user_id)}, expires_delta=access_token_expires
            )
            print(f"Access token created successfully")
        except Exception as token_error:
            print(f"Token creation error: {token_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token creation error: {str(token_error)}"
            )
        
        # Prepare user data for response
        print(f"Preparing user data response...")
        try:
            # Clean bio value
            bio_value = None
            if register_data.bio and register_data.bio.strip():
                bio_value = register_data.bio.strip()
            
            user_data = {
                "userid": int(user_id),  # Ensure it's an integer
                "username": str(register_data.username),
                "email": str(register_data.email),
                "profilepicurl": None,
                "bio": bio_value,  # Use cleaned bio value
                "createdat": datetime.now().isoformat()  # Convert to string for JSON serialization
            }
            print(f"User data prepared: {user_data}")
            print(f"User data types: {[(k, type(v)) for k, v in user_data.items()]}")
        except Exception as data_error:
            print(f"User data preparation error: {data_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data preparation error: {str(data_error)}"
            )
        
        print(f"Registration successful for user: {register_data.username}")
        
        # Create response object
        print(f"Creating AuthResponse object...")
        try:
            response = AuthResponse(
                access_token=access_token,
                user=user_data
            )
            print(f"AuthResponse created successfully")
            print(f"About to return response...")
            return response
        except Exception as response_error:
            print(f"Response creation error: {response_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response creation error: {str(response_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
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
        # Log user logout event using User model
        logout_event_data = {
            "username": current_user['username'],
            "logout_timestamp": datetime.now().isoformat(),
            "logout_method": "explicit_logout"
        }
        User.log_user_event(current_user['userid'], "UserLoggedOut", logout_event_data)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        print(f"Logout error: {e}")
        # Still return success message even if event logging fails
        return {"message": "Successfully logged out"}