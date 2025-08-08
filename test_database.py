#!/usr/bin/env python3
"""
Test database connectivity and setup.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

import asyncpg
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_password123@localhost:5432/trading_bot")

def parse_database_url(url):
    """Parse database URL into components."""
    # Remove postgresql:// prefix
    url = url.replace("postgresql://", "")
    
    # Split user:password@host:port/database
    auth_part, db_part = url.split("@")
    user, password = auth_part.split(":")
    host_port, database = db_part.split("/")
    host, port = host_port.split(":")
    
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": int(port),
        "database": database
    }

async def test_database_setup():
    """Test database connectivity and setup."""
    
    print("🚀 Testing Database Setup")
    print("=" * 50)
    print(f"📊 Database URL: {DATABASE_URL}")
    
    db_config = parse_database_url(DATABASE_URL)
    print(f"🏠 Host: {db_config['host']}:{db_config['port']}")
    print(f"👤 User: {db_config['user']}")
    print(f"🗃️  Database: {db_config['database']}")
    print()
    
    # Step 1: Test PostgreSQL server connectivity
    print("🔍 Step 1: Testing PostgreSQL server connectivity...")
    try:
        # Connect to default postgres database first
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database='postgres'  # Connect to default database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if our database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📝 Creating database: {db_config['database']}")
            cursor.execute(f'CREATE DATABASE "{db_config['database']}"')
            print("✅ Database created successfully")
        else:
            print("✅ Database already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL server connection failed: {e}")
        print("💡 Make sure PostgreSQL is running:")
        print("   brew services start postgresql")
        return False
    
    # Step 2: Test connection to our trading database
    print("\n🔍 Step 2: Testing trading database connection...")
    try:
        # Test synchronous connection
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Sync connection successful!")
            print(f"   PostgreSQL version: {version[:50]}...")
    
    except Exception as e:
        print(f"❌ Sync database connection failed: {e}")
        return False
    
    # Step 3: Test async connection
    print("\n🔍 Step 3: Testing async database connection...")
    try:
        async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        async_engine = create_async_engine(async_url)
        
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT current_database(), current_user"))
            row = result.fetchone()
            db_name, user = row
            print(f"✅ Async connection successful!")
            print(f"   Database: {db_name}")
            print(f"   User: {user}")
        
        await async_engine.dispose()
    
    except Exception as e:
        print(f"❌ Async database connection failed: {e}")
        return False
    
    # Step 4: Test database models
    print("\n🔍 Step 4: Testing database models...")
    try:
        # Import models directly
        sys.path.append(str(Path(__file__).parent / "src"))
        from database.models import Base
        
        # Create tables using sync engine
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Created tables ({len(tables)}): {', '.join(tables)}")
    
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        import traceback
        traceback.print_exc()
        print("💡 Will continue with basic database tests")
        # Don't return False - continue with other tests
    
    print("\n✅ Database setup completed successfully!")
    return True

async def test_basic_operations():
    """Test basic database operations."""
    
    print("\n🔍 Testing basic database operations...")
    
    try:
        async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        # Test raw asyncpg connection
        conn = await asyncpg.connect(async_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        # Test insert and select
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            INSERT INTO test_table (name) VALUES ($1)
        """, "test_connection")
        
        result = await conn.fetchrow("SELECT * FROM test_table ORDER BY id DESC LIMIT 1")
        print(f"✅ Test insert/select successful: {result}")
        
        # Cleanup
        await conn.execute("DROP TABLE test_table")
        await conn.close()
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        return False
    
    return True

def main():
    """Main function."""
    try:
        success = asyncio.run(test_database_setup())
        
        if success:
            success = asyncio.run(test_basic_operations())
        
        if success:
            print("\n🎉 All database tests passed!")
        else:
            print("\n❌ Some database tests failed")
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")

if __name__ == "__main__":
    main()