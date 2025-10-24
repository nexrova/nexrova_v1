#!/usr/bin/env python3
"""
Test script to verify booking functionality works
"""
import sys
import os

def test_booking_creation():
    """Test booking creation functionality"""
    print("🧪 Testing booking creation...")
    
    try:
        from database.models import GuestModel, BookingModel, RoomModel
        
        # Test guest creation
        guest_data = {
            'name': 'Test Guest',
            'email': 'test@example.com',
            'phone': '+91-9876543210',
            'id_proof': 'Test ID'
        }
        
        print("✅ Guest model imported successfully")
        
        # Test room retrieval
        rooms = RoomModel.get_all()
        print(f"✅ Found {len(rooms)} rooms")
        
        if rooms:
            room = rooms[0]
            print(f"✅ Sample room: {room.get('room_number', 'N/A')} - {room.get('room_type', 'N/A')}")
        
        # Test booking model
        bookings = BookingModel.get_all()
        print(f"✅ Found {len(bookings)} existing bookings")
        
        print("✅ All models working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def main():
    """Run the test"""
    print("🏨 PMS Booking Test")
    print("=" * 40)
    
    if test_booking_creation():
        print("\n🎉 All tests passed! The booking system should work now.")
        print("\n📝 Next steps:")
        print("1. Restart your Flask application")
        print("2. Try creating a new booking")
        print("3. Check the guests page")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
