"""
Initialize database - create all tables
Run this script to set up the database schema
"""
from database import init_db, engine
from models import Base

if __name__ == "__main__":
    print("🔄 Initializing database...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully!")
        print("📊 Tables created:")
        for table in Base.metadata.tables.keys():
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

