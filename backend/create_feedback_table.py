#!/usr/bin/env python3
"""
Script to create the Feedback table in the database
"""
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.database import engine, Base, Feedback

def create_feedback_table():
    """Create the Feedback table in the database"""
    try:
        print("🗄️  Creating Feedback table...")
        
        # Create the Feedback table
        Feedback.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Feedback table created successfully!")
        print("📋 Table structure:")
        print("   - FeedbackID (Primary Key, Auto-increment)")
        print("   - UserID (Foreign Key to Users)")
        print("   - OrganizationID (Foreign Key to Organizations)")
        print("   - SessionID (Chat session identifier)")
        print("   - MessageID (Message identifier within session)")
        print("   - UserMessage (NVARCHAR(4000) - Unicode support)")
        print("   - BotResponse (NVARCHAR(4000) - Unicode support)")
        print("   - Rating (1-5 rating)")
        print("   - Comment (NVARCHAR(1000) - Unicode support)")
        print("   - CreatedAt (Timestamp)")
        
    except Exception as e:
        print(f"❌ Error creating Feedback table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Feedback table creation...")
    success = create_feedback_table()
    
    if success:
        print("\n🎉 Feedback feature setup completed!")
        print("📝 Next steps:")
        print("   1. Restart your backend server")
        print("   2. Users can now provide feedback on chatbot responses")
        print("   3. Admins can view feedback in their dashboard")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
        sys.exit(1)
