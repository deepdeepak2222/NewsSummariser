"""
Database CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import User, UserPreference, SearchHistory
from schemas import UserCreate, UserPreferenceCreate, SearchHistoryCreate
from auth import get_password_hash


# User CRUD
def get_user_by_id(db: Session, user_id: int) -> User:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_username_or_email(db: Session, username_or_email: str) -> User:
    """Get user by username, email, or phone (for login)"""
    return db.query(User).filter(
        or_(
            User.username == username_or_email,
            User.email == username_or_email,
            User.phone == username_or_email
        )
    ).first()


def get_user_by_phone(db: Session, phone: str) -> User:
    """Get user by phone number"""
    return db.query(User).filter(User.phone == phone).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        phone=user.phone,
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        full_name=user.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default preferences
    create_user_preferences(db, db_user.id)
    
    return db_user


def update_user_last_login(db: Session, user_id: int):
    """Update user's last login timestamp"""
    user = get_user_by_id(db, user_id)
    if user:
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)


# User Preferences CRUD
def get_user_preferences(db: Session, user_id: int) -> UserPreference:
    """Get user preferences"""
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


def create_user_preferences(db: Session, user_id: int) -> UserPreference:
    """Create default user preferences"""
    preferences = UserPreference(
        user_id=user_id,
        language="English",
        theme="light",
        default_max_articles=10,
        email_notifications=False
    )
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences


def update_user_preferences(db: Session, user_id: int, preferences: UserPreferenceCreate) -> UserPreference:
    """Update user preferences"""
    db_preferences = get_user_preferences(db, user_id)
    if not db_preferences:
        db_preferences = create_user_preferences(db, user_id)
    
    for key, value in preferences.dict(exclude_unset=True).items():
        setattr(db_preferences, key, value)
    
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


# Search History CRUD
def create_search_history(db: Session, user_id: int, search: SearchHistoryCreate) -> SearchHistory:
    """Create search history entry"""
    db_search = SearchHistory(
        user_id=user_id,
        **search.dict()
    )
    db.add(db_search)
    db.commit()
    db.refresh(db_search)
    return db_search


def get_user_search_history(db: Session, user_id: int, limit: int = 20) -> list[SearchHistory]:
    """Get user's search history"""
    return db.query(SearchHistory)\
        .filter(SearchHistory.user_id == user_id)\
        .order_by(SearchHistory.created_at.desc())\
        .limit(limit)\
        .all()


def delete_search_history(db: Session, search_id: int, user_id: int) -> bool:
    """Delete a search history entry"""
    search = db.query(SearchHistory).filter(
        SearchHistory.id == search_id,
        SearchHistory.user_id == user_id
    ).first()
    
    if search:
        db.delete(search)
        db.commit()
        return True
    return False

