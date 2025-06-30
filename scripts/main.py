from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import uuid
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# Initialize FastAPI app
app = FastAPI(title="Car Selling API", version="1.0.0", 
              description="This is the fast API for testing with jwt in NextJs, and author by S.Sokcheat")

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "a88e2f0119f801637e022ea0ea364c18c104c0e110b31b9cdb03f609b9a96fb4")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
REFRESH_TOKEN_EXPIRE_DAYS = 1

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://caruser:carpass@localhost:5432/cardb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CarDB(Base):
    __tablename__ = "cars"
    
    id = Column(String, primary_key=True, index=True)
    make = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer)
    price = Column(Float)
    mileage = Column(Integer)
    description = Column(Text)
    color = Column(String)
    fuel_type = Column(String)
    transmission = Column(String)
    image = Column(String)  
    seller_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_sold = Column(Boolean, default=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirmed_password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

class UploadResponse(BaseModel):
    filename: str
    url: str
    message: str

class CarCreate(BaseModel):
    make: str
    model: str
    year: int
    price: float
    mileage: int
    description: Optional[str] = None
    color: str
    fuel_type: str
    transmission: str
    image: str

class Car(BaseModel):
    id: str
    make: str
    model: str
    year: int
    price: float
    mileage: int
    description: Optional[str] = None
    color: str
    fuel_type: str
    transmission: str
    seller_id: str
    created_at: datetime
    image: str
    is_sold: bool = False

class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    description: Optional[str] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    image: Optional[str] = None
    is_sold: Optional[bool] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Verify it's an access token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# Authentication endpoints
@app.post("/register", response_model=User, tags=["auths"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email has already registered"
        )
    if(user.password != user.confirmed_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "This confirmed password does not match"
        )
    hashed_password = get_password_hash(user.password)
    
    user_id = str(uuid.uuid4())
    
    db_user = UserDB(
        id=user_id,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at
    )

@app.post("/login", response_model=Token,tags=["auths"])
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@app.get("/me", response_model=User, tags=["me"])
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )

# Car endpoints
@app.post("/cars", response_model=Car, tags=["cars"])
async def create_car(car: CarCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    car_id = str(uuid.uuid4())
    
    db_car = CarDB(
        id=car_id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=current_user.id
    )
    
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    
    return Car(
        id=db_car.id,
        make=db_car.make,
        model=db_car.model,
        year=db_car.year,
        price=db_car.price,
        mileage=db_car.mileage,
        description=db_car.description,
        color=db_car.color,
        fuel_type=db_car.fuel_type,
        transmission=db_car.transmission,
        image=db_car.image,
        seller_id=db_car.seller_id,
        created_at=db_car.created_at,
        is_sold=db_car.is_sold
    )

@app.post("/cars/upload", response_model=Car, tags=["cars"])
async def upload_car_with_image(
    make: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    price: float = Form(...),
    mileage: int = Form(...),
    color: str = Form(...),
    fuel_type: str = Form(...),
    transmission: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a car with image in one request
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix.lower()
    if not file_extension:
        file_extension = ".jpg"  # Default extension
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Generate URL for accessing the image
        image_url = f"/uploads/{unique_filename}"
        
        # Create car record
        car_id = str(uuid.uuid4())
        
        db_car = CarDB(
            id=car_id,
            make=make,
            model=model,
            year=year,
            price=price,
            mileage=mileage,
            description=description,
            color=color,
            fuel_type=fuel_type,
            transmission=transmission,
            image=image_url,
            seller_id=current_user.id
        )
        
        db.add(db_car)
        db.commit()
        db.refresh(db_car)
        
        return Car(
            id=db_car.id,
            make=db_car.make,
            model=db_car.model,
            year=db_car.year,
            price=db_car.price,
            mileage=db_car.mileage,
            description=db_car.description,
            color=db_car.color,
            fuel_type=db_car.fuel_type,
            transmission=db_car.transmission,
            image=db_car.image,
            seller_id=db_car.seller_id,
            created_at=db_car.created_at,
            is_sold=db_car.is_sold
        )
        
    except Exception as e:
        # Clean up uploaded file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create car: {str(e)}"
        )

@app.post("/access-token", response_model=Token, tags=["auths"])
async def get_access_token(user: UserLogin, db: Session = Depends(get_db)):
    """
    Alternative endpoint to get access token - same as login but with different endpoint name
    """
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@app.post("/refresh-token", response_model=Token, tags=["auths"])
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Verify it's a refresh token
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Check if user exists
        user = db.query(UserDB).filter(UserDB.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        # Create new tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            data={"sub": email}, expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/cars", response_model=List[Car], tags=["cars"])
async def get_cars(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cars = db.query(CarDB).offset(skip).limit(limit).all()
    return [Car(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=car.seller_id,
        created_at=car.created_at,
        is_sold=car.is_sold
    ) for car in cars]

@app.get("/cars/{car_id}", response_model=Car, tags=["cars"])
async def get_car(car_id: str, db: Session = Depends(get_db)):
    car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    return Car(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=car.seller_id,
        created_at=car.created_at,
        is_sold=car.is_sold
    )

@app.get("/my-cars", response_model=List[Car], tags=["cars"])
async def get_my_cars(current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    cars = db.query(CarDB).filter(CarDB.seller_id == current_user.id).all()
    return [Car(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=car.seller_id,
        created_at=car.created_at,
        is_sold=car.is_sold
    ) for car in cars]

@app.put("/cars/{car_id}", response_model=Car, tags=["cars"])
async def update_car(car_id: str, car_update: CarUpdate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Update car information by ID
    """
    car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    if car.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this car"
        )
    
    update_data = car_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(car, field, value)
    
    db.commit()
    db.refresh(car)
    
    return Car(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=car.seller_id,
        created_at=car.created_at,
        is_sold=car.is_sold
    )

@app.put("/cars/{car_id}/upload", response_model=Car, tags=["cars"])
async def update_car_with_image(
    car_id: str,
    make: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    price: Optional[float] = Form(None),
    mileage: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    fuel_type: Optional[str] = Form(None),
    transmission: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_sold: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update car information and/or image by ID
    """
    car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    if car.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this car"
        )
    
    # Handle image upload if provided
    image_url = car.image  # Keep existing image by default
    old_image_path = None
    
    if file:
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 5MB."
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        if not file_extension:
            file_extension = ".jpg"  # Default extension
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save new file
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            
            # Store old image path for cleanup
            if car.image and car.image.startswith("/uploads/"):
                old_filename = car.image.replace("/uploads/", "")
                old_image_path = UPLOAD_DIR / old_filename
            
            # Generate new URL
            image_url = f"/uploads/{unique_filename}"
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    # Update car fields
    update_fields = {
        "make": make,
        "model": model,
        "year": year,
        "price": price,
        "mileage": mileage,
        "color": color,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "description": description,
        "is_sold": is_sold,
        "image": image_url
    }
    
    # Only update fields that are provided
    for field, value in update_fields.items():
        if value is not None:
            setattr(car, field, value)
    
    try:
        db.commit()
        db.refresh(car)
        
        # Clean up old image file if a new one was uploaded
        if old_image_path and old_image_path.exists():
            old_image_path.unlink()
        
        return Car(
            id=car.id,
            make=car.make,
            model=car.model,
            year=car.year,
            price=car.price,
            mileage=car.mileage,
            description=car.description,
            color=car.color,
            fuel_type=car.fuel_type,
            transmission=car.transmission,
            image=car.image,
            seller_id=car.seller_id,
            created_at=car.created_at,
            is_sold=car.is_sold
        )
        
    except Exception as e:
        # Clean up new uploaded file if database operation fails
        if file and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update car: {str(e)}"
        )

@app.delete("/cars/{car_id}", tags=["cars"])
async def delete_car(car_id: str, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    car = db.query(CarDB).filter(CarDB.id == car_id).first()
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    if car.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this car"
        )
    
    db.delete(car)
    db.commit()
    return {"message": "Car deleted successfully"}


@app.get("/cars/search/{query}", response_model=List[Car], tags=["cars"])
async def search_cars(query: str, db: Session = Depends(get_db)):
    cars = db.query(CarDB).filter(
        (CarDB.make.ilike(f"%{query}%")) |
        (CarDB.model.ilike(f"%{query}%")) |
        (CarDB.color.ilike(f"%{query}%")) |
        (CarDB.description.ilike(f"%{query}%"))
    ).all()
    
    return [Car(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        price=car.price,
        mileage=car.mileage,
        description=car.description,
        color=car.color,
        fuel_type=car.fuel_type,
        transmission=car.transmission,
        image=car.image,
        seller_id=car.seller_id,
        created_at=car.created_at,
        is_sold=car.is_sold
    ) for car in cars]

@app.post("/upload", response_model=UploadResponse, tags=["upload"])
async def upload_car_image(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Upload car image file and return the URL
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix.lower()
    if not file_extension:
        file_extension = ".jpg"  # Default extension
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Generate URL for accessing the image
        image_url = f"/uploads/{unique_filename}"
        
        return UploadResponse(
            filename=unique_filename,
            url=image_url,
            message="Image uploaded successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@app.delete("/upload/{filename}", tags=["upload"])
async def delete_car_image(
    filename: str,
    current_user: UserDB = Depends(get_current_user)
):
    """
    Delete uploaded car image file
    """
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    try:
        file_path.unlink()  # Delete the file
        return {"message": f"Image {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "Car Selling API",
        "version": "1.0.0",
        "endpoints": {
            "auth": ["/register", "/login", "/access-token", "/refresh-token", "/me"],
            "cars": [
                "/cars", 
                "/cars/upload", 
                "/cars/{id}", 
                "/cars/{id}/upload", 
                "/my-cars", 
                "/cars/search/{query}"
            ],
            "upload": ["/upload", "/upload/{filename}"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8998)
