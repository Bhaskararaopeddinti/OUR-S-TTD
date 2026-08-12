"""
Script to find and remove guest accounts from the database
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ours_ttd.db")

print(f"Connecting to database: {DATABASE_URL.replace(os.getenv('SECRET_KEY', 'secret'), '***') if 'postgres' in DATABASE_URL else DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Find guest accounts
    guest_query = text("""
        SELECT id, name, email, role, created_at 
        FROM users 
        WHERE name LIKE '%guest%' 
           OR email LIKE '%guest%' 
           OR role = 'guest'
        ORDER BY created_at
    """)
    
    guest_users = session.execute(guest_query).fetchall()
    
    if guest_users:
        print("\nFound guest accounts:")
        print("-" * 80)
        for user in guest_users:
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}, Created: {user.created_at}")
        print("-" * 80)
        
        # Ask for confirmation
        response = input(f"\nFound {len(guest_users)} guest account(s). Do you want to delete them? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            # Delete guest accounts
            for user in guest_users:
                user_id = user.id
                print(f"Deleting user ID {user_id}...")
                
                # Delete related records first (cascade should handle this, but let's be explicit)
                session.execute(text("DELETE FROM health_reminders WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM lost_found WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM notifications WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM chat_history WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM bookings WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM pilgrim_profiles WHERE user_id = :user_id"), {"user_id": user_id})
                session.execute(text("DELETE FROM emergency_alerts WHERE user_id = :user_id"), {"user_id": user_id})
                
                # Delete the user
                session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            
            session.commit()
            print(f"Successfully deleted {len(guest_users)} guest account(s)")
        else:
            print("Deletion cancelled")
    else:
        print("No guest accounts found in the database")
        
except Exception as e:
    print(f"Error: {e}")
    session.rollback()
finally:
    session.close()
    engine.dispose()
