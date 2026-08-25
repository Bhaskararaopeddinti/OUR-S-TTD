"""
Script to list all users in the database
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
    # List all users
    users_query = text("""
        SELECT id, name, email, role, created_at 
        FROM users 
        ORDER BY created_at
    """)
    
    all_users = session.execute(users_query).fetchall()
    
    if all_users:
        print(f"\nTotal users found: {len(all_users)}")
        print("-" * 100)
        print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Role':<15} {'Created At':<20}")
        print("-" * 100)
        for user in all_users:
            print(f"{user.id:<5} {user.name:<20} {user.email:<30} {user.role:<15} {str(user.created_at):<20}")
        print("-" * 100)
    else:
        print("No users found in the database")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
    engine.dispose()
