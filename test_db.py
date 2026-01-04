#!/usr/bin/env python3
"""Test database connection and session handling."""
from storage.database import get_db
from storage.prompt_storage import PromptStorage

def test_database():
    """Test that database session works correctly."""
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        print("✓ Database session created successfully")
        print(f"  Session type: {type(db).__name__}")
        
        # Test PromptStorage
        storage = PromptStorage(db)
        print("✓ PromptStorage initialized")
        
        # Test query
        versions = storage.list_versions()
        print(f"✓ Query executed successfully - found {len(versions)} prompt versions")
        
        # Close session
        try:
            next(db_gen)  # This should raise StopIteration
        except StopIteration:
            pass
        
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database()


