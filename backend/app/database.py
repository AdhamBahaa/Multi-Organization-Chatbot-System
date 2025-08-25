from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean, NVARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER")    
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER")

DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?driver={DB_DRIVER}&charset=utf8&unicode_results=true"

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
    isActivated = Column(Integer, default=0, nullable=False)  # Track if admin has set their password (0=False, 1=True)
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    organization = relationship("Organization", back_populates="admins")
    users = relationship("User", back_populates="admin", cascade="all, delete-orphan")
    
    @property
    def is_activated_bool(self):
        """Convert integer/string to Python boolean"""
        if self.isActivated is None:
            return False
        # Convert to integer first to handle both string and integer values
        try:
            return int(self.isActivated) == 1
        except (ValueError, TypeError):
            return False

class User(Base):
    __tablename__ = "Users"
    
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    AdminID = Column(Integer, ForeignKey("Admins.AdminID"), nullable=False)
    OrganizationID = Column(Integer, ForeignKey("Organizations.OrganizationID"), nullable=False)
    FullName = Column(String(255), nullable=False)
    Email = Column(String(255), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=True)  # Can be null initially
    Role = Column(String(100), nullable=False, default="Member")  # Default to 'Member'
    isActivated = Column(Integer, default=0, nullable=False)  # Track if user has set their password (0=False, 1=True)
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    admin = relationship("Admin", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_activated_bool(self):
        """Convert integer/string to Python boolean"""
        if self.isActivated is None:
            return False
        # Convert to integer first to handle both string and integer values
        try:
            return int(self.isActivated) == 1
        except (ValueError, TypeError):
            return False

class Feedback(Base):
    __tablename__ = "Feedback"
    
    FeedbackID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    OrganizationID = Column(Integer, ForeignKey("Organizations.OrganizationID"), nullable=False)
    SessionID = Column(Integer, nullable=False)  # Chat session ID
    MessageID = Column(Integer, nullable=False)  # Message ID within the session
    UserMessage = Column(NVARCHAR(4000), nullable=False)  # User's original message
    BotResponse = Column(NVARCHAR(4000), nullable=False)  # Bot's response
    Rating = Column(Integer, nullable=False)  # 1-5 rating (1=very poor, 5=excellent)
    Comment = Column(NVARCHAR(1000), nullable=True)  # Optional comment from user
    CreatedAt = Column(DateTime, default=func.getdate())
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    organization = relationship("Organization")

# Chat History Models
class ChatSession(Base):
    __tablename__ = "ChatSessions"
    
    SessionID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    OrganizationID = Column(Integer, ForeignKey("Organizations.OrganizationID"), nullable=False)
    Title = Column(NVARCHAR(255), nullable=True)  # Auto-generated title from first message
    CreatedAt = Column(DateTime, default=func.getdate())
    UpdatedAt = Column(DateTime, default=func.getdate(), onupdate=func.getdate())
    IsActive = Column(Boolean, default=True)  # To mark sessions as active/inactive
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    organization = relationship("Organization")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "ChatMessages"
    
    MessageID = Column(Integer, primary_key=True, autoincrement=True)
    SessionID = Column(Integer, ForeignKey("ChatSessions.SessionID"), nullable=False)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    Role = Column(String(20), nullable=False)  # "user" or "assistant"
    Content = Column(NVARCHAR(4000), nullable=False)
    Timestamp = Column(DateTime, default=func.getdate())
    MessageOrder = Column(Integer, nullable=False)  # Order within the session
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")

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