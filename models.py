"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)  # Optional
    phone = Column(String(20), unique=True, index=True, nullable=False)  # Mandatory
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    saved_summaries = relationship("SavedSummary", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("NewsAlert", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    language = Column(String(10), default="English")
    theme = Column(String(10), default="light")
    default_location = Column(String(255))
    default_max_articles = Column(Integer, default=10)
    email_notifications = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="preferences")


class SearchHistory(Base):
    """User search history"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    location = Column(String(255))
    max_articles = Column(Integer)
    language = Column(String(10))
    when_filter = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="search_history")


class SavedSummary(Base):
    """Saved summaries/bookmarks"""
    __tablename__ = "saved_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    articles = Column(Text)  # JSON string of articles
    language = Column(String(10))
    source_count = Column(Integer)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="saved_summaries")


class NewsAlert(Base):
    """News alerts for users"""
    __tablename__ = "news_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    location = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    notify_email = Column(Boolean, default=True)
    notify_browser = Column(Boolean, default=False)
    frequency = Column(String(20), default="daily")
    last_notified = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="alerts")

