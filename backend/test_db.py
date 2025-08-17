"""
Database connection test script
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        from database import engine, SessionLocal, Organization, Admin, User
        
        print("🔌 Testing database connection...")
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Test session creation
        db = SessionLocal()
        print("✅ Database session created successfully!")
        
        # Test basic queries
        org_count = db.query(Organization).count()
        admin_count = db.query(Admin).count()
        user_count = db.query(User).count()
        
        print(f"📊 Current database state:")
        print(f"   Organizations: {org_count}")
        print(f"   Admins: {admin_count}")
        print(f"   Users: {user_count}")
        
        # Show organization structure
        if org_count > 0:
            print(f"\n🏢 Organization Structure:")
            organizations = db.query(Organization).all()
            for org in organizations:
                admin_count = db.query(Admin).filter(Admin.OrganizationID == org.OrganizationID).count()
                user_count = db.query(User).filter(User.OrganizationID == org.OrganizationID).count()
                print(f"   {org.Name}: {admin_count} admins, {user_count} users")
                
                # Show admins in this organization
                admins = db.query(Admin).filter(Admin.OrganizationID == org.OrganizationID).all()
                for admin in admins:
                    admin_user_count = db.query(User).filter(User.AdminID == admin.AdminID).count()
                    print(f"     └─ {admin.FullName} ({admin.Email}): {admin_user_count} users")
                    
                    # Show users under this admin with their roles
                    users = db.query(User).filter(User.AdminID == admin.AdminID).all()
                    for user in users:
                        print(f"        └─ {user.FullName} ({user.Email}) - Role: {user.Role}")
        
        db.close()
        print("\n✅ Database test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if SQL Server is running")
        print("2. Verify database credentials in .env file")
        print("3. Ensure ODBC Driver 17 is installed")
        print("4. Check if the 'chatbot' database exists")
        print("5. Verify the database tables are created")

if __name__ == "__main__":
    test_database_connection()
