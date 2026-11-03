"""
Appointment Booking System - Backend
FastAPI + SQLite + JWT Authentication
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# ============ Configuration ============
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_" + os.urandom(16).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")  # must be set in the runtime environment

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookings.db")

# ============ Database ============
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    service = Column(String, nullable=False)
    preferred_date = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String, default="New")  # New / Contacted / Confirmed / Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ Data models ============
class BookingCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr
    service: str
    preferred_date: str
    details: Optional[str] = None


class BookingOut(BookingCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ============ Authentication ============
def verify_admin(username: str, password: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    if username != ADMIN_USERNAME:
        return False
    # The password is compared with the hash stored in ADMIN_PASSWORD_HASH when available,
    # otherwise it is compared directly for initial setup only; always prefer a hash in production
    admin_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if admin_hash:
        return pwd_context.verify(password, admin_hash)
    return password == ADMIN_PASSWORD


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials or expired session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


# ============ Application ============
app = FastAPI(title="Appointment Booking System", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prefer restricting this to the production website origin after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "booking-system"}


@app.post("/api/bookings", response_model=BookingOut, status_code=201)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """Receive a new appointment from the public website - unauthenticated endpoint"""
    new_booking = Booking(**booking.model_dump())
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


@app.post("/api/admin/login", response_model=Token)
def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Admin login - returns a JWT token"""
    if not verify_admin(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/admin/bookings", response_model=List[BookingOut])
def list_bookings(
    db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)
):
    """List all appointments - authentication required"""
    return db.query(Booking).order_by(Booking.created_at.desc()).all()


@app.patch("/api/admin/bookings/{booking_id}", response_model=BookingOut)
def update_booking_status(
    booking_id: int,
    update: StatusUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """Update an appointment status - authentication required"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found")
    booking.status = update.status
    db.commit()
    db.refresh(booking)
    return booking


@app.delete("/api/admin/bookings/{booking_id}", status_code=204)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """Delete an appointment - authentication required"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(booking)
    db.commit()
    return None
