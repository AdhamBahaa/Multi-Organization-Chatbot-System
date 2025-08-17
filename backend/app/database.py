from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "")    
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "DESKTOP-HHVQ12U\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "chatbot")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC+Driver+17+for+SQL+Server")

DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?driver={DB_DRIVER}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database Models
class Organization(Base):
    __tablename__ = "Organizations"
    
    OrganizationID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(255), nullable=False)
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    admins = relationship("Admin", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")

class Admin(Base):
    __tablename__ = "Admins"
    
    AdminID = Column(Integer, primary_key=True, autoincrement=True)
    OrganizationID = Column(Integer, ForeignKey("Organizations.OrganizationID"), nullable=False)
    FullName = Column(String(255), nullable=False)
    Email = Column(String(255), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=True)  # Can be null initially
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    organization = relationship("Organization", back_populates="admins")
    users = relationship("User", back_populates="admin", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "Users"
    
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    AdminID = Column(Integer, ForeignKey("Admins.AdminID"), nullable=False)
    OrganizationID = Column(Integer, ForeignKey("Organizations.OrganizationID"), nullable=False)
    FullName = Column(String(255), nullable=False)
    Email = Column(String(255), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=True)  # Can be null initially
    Role = Column(String(100), nullable=False, default="Member")  # Default to 'Member'
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    admin = relationship("Admin", back_populates="users")
    organization = relationship("Organization", back_populates="users")

# Function to create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()