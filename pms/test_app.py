#!/usr/bin/env python3
"""
Simple test script to verify the PMS application works
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from pms_app import create_app
        print("✅ Main app import successful")
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    try:
        from config import Config
        print("✅ Config import successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from database.models import RoomModel, GuestModel, BookingModel, OccupancyModel
        print("✅ Database models import successful")
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        return False
    
    try:
        from routes.web_routes import web_bp
        from routes.api_routes import api_bp
        print("✅ Routes import successful")
    except Exception as e:
        print(f"❌ Routes import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test if the Flask app can be created"""
    print("\n🧪 Testing app creation...")
    
    try:
        from pms_app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Test if routes are registered
        with app.app_context():
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            print(f"✅ Found {len(rules)} routes registered")
            
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_database_models():
    """Test database models with sample data"""
    print("\n🧪 Testing database models...")
    
    try:
        from database.models import RoomModel, OccupancyModel
        
        # Test room model
        rooms = RoomModel.get_all()
        print(f"✅ RoomModel.get_all() returned {len(rooms)} rooms")
        
        # Test occupancy model
        stats = OccupancyModel.get_stats()
        print(f"✅ OccupancyModel.get_stats() returned stats: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏨 Hotel PMS - Application Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_creation,
        test_database_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the application:")
        print("   python run.py")
        print("   or")
        print("   python pms_app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
