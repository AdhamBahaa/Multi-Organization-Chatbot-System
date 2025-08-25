#!/usr/bin/env python3
"""
Script to drop the Feedback table in the database
"""
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.database import engine, Base, Feedback

def drop_feedback_table():
    """Drop the Feedback table in the database"""
    try:
        print("🗑️  Dropping Feedback table...")
        
        # Drop the Feedback table
        Feedback.__table__.drop(bind=engine, checkfirst=True)
        
        print("✅ Feedback table dropped successfully!")
        
    except Exception as e:
        print(f"❌ Error dropping Feedback table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Feedback table drop...")
    success = drop_feedback_table()
    
    if success:
        print("\n🎉 Feedback table dropped successfully!")
        print("📝 Next steps:")
        print("   1. Run create_feedback_table.py to recreate with Unicode support")
        print("   2. Restart your backend server")
    else:
        print("\n💥 Drop failed. Please check the error messages above.")
        sys.exit(1)
