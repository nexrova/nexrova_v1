"""
Database models and operations for Hotel PMS
Handles all interactions with Supabase PostgreSQL database
"""
from datetime import datetime
from typing import List, Dict, Optional
from database.db import get_supabase
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoomModel:
    """Room database operations"""

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all rooms"""
        try:
            supabase = get_supabase()
            response = supabase.table('rooms').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting rooms: {e}")
            # Return sample data for development
            return [
                {
                    'room_id': 1,
                    'room_number': '101',
                    'room_type': 'Deluxe',
                    'floor': 1,
                    'base_price': 5000.0,
                    'status': 'available',
                    'amenities': ['WiFi', 'AC', 'TV'],
                    'current_guest_id': None,
                    'current_booking_id': None
                },
                {
                    'room_id': 2,
                    'room_number': '102',
                    'room_type': 'Standard',
                    'floor': 1,
                    'base_price': 3000.0,
                    'status': 'available',
                    'amenities': ['WiFi', 'AC'],
                    'current_guest_id': None,
                    'current_booking_id': None
                }
            ]

    @staticmethod
    def get_by_id(room_id: int) -> Optional[Dict]:
        """Get room by ID"""
        try:
            supabase = get_supabase()
            response = supabase.table('rooms').select('*').eq('room_id', room_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting room {room_id}: {e}")
            return None

    @staticmethod
    def get_with_guest_details(room_id: int) -> Optional[Dict]:
        """Get room with current guest information"""
        try:
            supabase = get_supabase()
            
            # Get room data
            room_response = supabase.table('rooms').select('*').eq('room_id', room_id).execute()
            
            if not room_response.data:
                return None
            
            room = room_response.data[0]  # Get first (and should be only) room
            
            # If room has a current guest, fetch guest and booking details
            if room.get('current_guest_id'):
                guest_response = supabase.table('guests').select('*').eq(
                    'guest_id', room['current_guest_id']
                ).execute()
                
                booking_response = supabase.table('bookings').select('*').eq(
                    'booking_id', room['current_booking_id']
                ).execute()
                
                if guest_response.data and booking_response.data:
                    guest = guest_response.data[0]
                    booking = booking_response.data[0]
                    
                    room['current_guest'] = {
                        'guest_id': guest['guest_id'],
                        'name': guest['name'],
                        'email': guest['email'],
                        'phone': guest['phone'],
                        'check_in': booking['check_in'],
                        'check_out': booking['check_out'],
                        'booking_id': booking['booking_id']
                    }
                else:
                    room['current_guest'] = None
            else:
                room['current_guest'] = None
            
            return room
        except Exception as e:
            logger.error(f"Error getting room with guest details {room_id}: {e}")
            return None

    @staticmethod
    def get_all_with_guest_details() -> List[Dict]:
        """Get all rooms with guest information"""
        try:
            rooms = RoomModel.get_all()
            result = []
            
            for room in rooms:
                room_with_guest = RoomModel.get_with_guest_details(room['room_id'])
                if room_with_guest:
                    result.append(room_with_guest)
            
            return result
        except Exception as e:
            logger.error(f"Error getting rooms with guest details: {e}")
            return []

    @staticmethod
    def update(room_id: int, data: Dict) -> Optional[Dict]:
        """Update room details"""
        try:
            supabase = get_supabase()
            response = supabase.table('rooms').update(data).eq('room_id', room_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating room {room_id}: {e}")
            return None

    @staticmethod
    def update_status(room_id: int, status: str, guest_id: Optional[int] = None, 
                     booking_id: Optional[int] = None) -> Optional[Dict]:
        """Update room status and occupancy"""
        data = {
            'status': status,
            'current_guest_id': guest_id,
            'current_booking_id': booking_id
        }
        return RoomModel.update(room_id, data)

    @staticmethod
    def check_availability(room_id: int, check_in: str, check_out: str) -> bool:
        """Check if room is available for given dates"""
        supabase = get_supabase()
        
        # Get overlapping bookings
        response = supabase.table('bookings').select('*').eq(
            'room_id', room_id
        ).in_('status', ['confirmed', 'checked_in']).execute()
        
        check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
        
        for booking in response.data:
            booking_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
            booking_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')
            
            # Check for overlap
            if check_in_dt < booking_out and check_out_dt > booking_in:
                return False
        
        return True

    @staticmethod
    def get_available_rooms(check_in: str, check_out: str) -> List[Dict]:
        """Get all available rooms for given dates"""
        all_rooms = RoomModel.get_all()
        available = []
        
        for room in all_rooms:
            if room['status'] != 'maintenance' and RoomModel.check_availability(
                room['room_id'], check_in, check_out
            ):
                available.append(room)
        
        return available

class GuestModel:
    """Guest database operations"""

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all guests"""
        supabase = get_supabase()
        response = supabase.table('guests').select('*').execute()
        return response.data

    @staticmethod
    def get_by_id(guest_id: int) -> Optional[Dict]:
        """Get guest by ID"""
        try:
            supabase = get_supabase()
            response = supabase.table('guests').select('*').eq('guest_id', guest_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting guest {guest_id}: {e}")
            return None

    @staticmethod
    def create(guest_data: Dict) -> Dict:
        """Create new guest"""
        try:
            supabase = get_supabase()
            
            data = {
                'name': guest_data['name'],
                'email': guest_data['email'],
                'phone': guest_data['phone'],
                'id_proof': guest_data.get('id_proof', ''),
                'created_at': datetime.now().isoformat()
            }
            
            response = supabase.table('guests').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating guest: {e}")
            # If it's a duplicate email error, try to get the existing guest
            if 'duplicate key value violates unique constraint' in str(e):
                try:
                    existing_guest = supabase.table('guests').select('*').eq('email', guest_data['email']).execute()
                    if existing_guest.data:
                        return existing_guest.data[0]
                except:
                    pass
            raise e

    @staticmethod
    def get_with_booking_details(guest_id: int) -> Optional[Dict]:
        """Get guest with all booking history and current room"""
        guest = GuestModel.get_by_id(guest_id)
        
        if not guest:
            return None
        
        supabase = get_supabase()
        
        # Get all bookings for this guest
        bookings_response = supabase.table('bookings').select('*').eq(
            'guest_id', guest_id
        ).execute()
        
        # Enrich bookings with room information
        enriched_bookings = []
        current_booking = None
        
        for booking in bookings_response.data:
            room = RoomModel.get_by_id(booking['room_id'])
            
            enriched_booking = {
                **booking,
                'room_number': room['room_number'] if room else None,
                'room_type': room['room_type'] if room else None
            }
            
            enriched_bookings.append(enriched_booking)
            
            # Find current active booking
            if booking['status'] in ['confirmed', 'checked_in']:
                current_booking = enriched_booking
        
        guest['bookings'] = enriched_bookings
        guest['current_booking'] = current_booking
        
        if current_booking:
            room = RoomModel.get_by_id(current_booking['room_id'])
            guest['current_room'] = {
                'room_id': room['room_id'],
                'room_number': room['room_number'],
                'room_type': room['room_type']
            } if room else None
        else:
            guest['current_room'] = None
        
        return guest

    @staticmethod
    def get_all_with_booking_details() -> List[Dict]:
        """Get all guests with their booking details"""
        try:
            guests = GuestModel.get_all()
            result = []
            
            for guest in guests:
                guest_with_bookings = GuestModel.get_with_booking_details(guest['guest_id'])
                if guest_with_bookings:
                    result.append(guest_with_bookings)
            
            return result
        except Exception as e:
            logger.error(f"Error getting guests with booking details: {e}")
            return []

    @staticmethod
    def get_checked_in_guests() -> List[Dict]:
        """Get all currently checked-in guests with room details"""
        supabase = get_supabase()
        
        # Get all checked-in bookings
        bookings_response = supabase.table('bookings').select('*').eq(
            'status', 'checked_in'
        ).execute()
        
        checked_in = []
        
        for booking in bookings_response.data:
            guest = GuestModel.get_by_id(booking['guest_id'])
            room = RoomModel.get_by_id(booking['room_id'])
            
            if guest and room:
                checked_in.append({
                    'guest_id': guest['guest_id'],
                    'guest_name': guest['name'],
                    'guest_email': guest['email'],
                    'guest_phone': guest['phone'],
                    'room_id': room['room_id'],
                    'room_number': room['room_number'],
                    'room_type': room['room_type'],
                    'booking_id': booking['booking_id'],
                    'check_in': booking['check_in'],
                    'check_out': booking['check_out'],
                    'checked_in_at': booking.get('checked_in_at')
                })
        
        return checked_in

class BookingModel:
    """Booking database operations"""

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all bookings"""
        supabase = get_supabase()
        response = supabase.table('bookings').select('*').execute()
        return response.data

    @staticmethod
    def get_by_id(booking_id: int) -> Optional[Dict]:
        """Get booking by ID"""
        try:
            supabase = get_supabase()
            response = supabase.table('bookings').select('*').eq(
                'booking_id', booking_id
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting booking {booking_id}: {e}")
            return None

    @staticmethod
    def create(booking_data: Dict) -> Dict:
        """Create new booking"""
        try:
            supabase = get_supabase()
            
            data = {
                'room_id': booking_data['room_id'],
                'guest_id': booking_data['guest_id'],
                'check_in': booking_data['check_in'],
                'check_out': booking_data['check_out'],
                'total_price': booking_data['total_price'],
                'status': 'confirmed',
                'created_at': datetime.now().isoformat()
            }
            
            response = supabase.table('bookings').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise e

    @staticmethod
    def update_status(booking_id: int, new_status: str) -> Optional[Dict]:
        """Update booking status with proper room management"""
        booking = BookingModel.get_by_id(booking_id)
        
        if not booking:
            return None
        
        supabase = get_supabase()
        old_status = booking['status']
        
        # Update booking status
        update_data = {'status': new_status}
        
        # Handle status transitions
        if new_status == 'checked_in' and old_status != 'checked_in':
            # Guest checking in - mark room as occupied
            update_data['checked_in_at'] = datetime.now().isoformat()
            
            # Update room status
            RoomModel.update_status(
                booking['room_id'],
                'occupied',
                guest_id=booking['guest_id'],
                booking_id=booking_id
            )
        
        elif new_status == 'checked_out' and old_status == 'checked_in':
            # Guest checking out
            update_data['checked_out_at'] = datetime.now().isoformat()
            
            # Check if there's a same-day check-in
            today = datetime.now().strftime('%Y-%m-%d')
            next_bookings = supabase.table('bookings').select('*').eq(
                'room_id', booking['room_id']
            ).eq('check_in', today).eq('status', 'confirmed').execute()
            
            # Filter out current booking
            next_bookings_filtered = [
                b for b in next_bookings.data if b['booking_id'] != booking_id
            ]
            
            if next_bookings_filtered:
                # Auto check-in next guest
                next_booking = next_bookings_filtered
                BookingModel.update_status(next_booking['booking_id'], 'checked_in')
            else:
                # No next booking - mark room as available
                RoomModel.update_status(booking['room_id'], 'available')
        
        elif new_status == 'cancelled':
            # Booking cancelled
            if old_status == 'checked_in':
                # If checked in, treat as check-out
                update_data['checked_out_at'] = datetime.now().isoformat()
                RoomModel.update_status(booking['room_id'], 'available')
        
        # Update the booking
        response = supabase.table('bookings').update(update_data).eq(
            'booking_id', booking_id
        ).execute()
        
        return response.data[0] if response.data else None

    @staticmethod
    def get_all_enriched() -> List[Dict]:
        """Get all bookings with room and guest details"""
        bookings = BookingModel.get_all()
        enriched = []
        
        for booking in bookings:
            room = RoomModel.get_by_id(booking['room_id'])
            guest = GuestModel.get_by_id(booking['guest_id'])
            
            enriched.append({
                **booking,
                'room_number': room['room_number'] if room else 'N/A',
                'room_type': room['room_type'] if room else 'N/A',
                'guest_name': guest['name'] if guest else 'N/A',
                'guest_email': guest['email'] if guest else 'N/A',
                'guest_phone': guest['phone'] if guest else 'N/A'
            })
        
        return enriched

    @staticmethod
    def get_enriched(booking_id: int) -> Optional[Dict]:
        """Get single booking with room and guest details"""
        booking = BookingModel.get_by_id(booking_id)
        
        if not booking:
            return None
        
        room = RoomModel.get_by_id(booking['room_id'])
        guest = GuestModel.get_by_id(booking['guest_id'])
        
        return {
            **booking,
            'room_number': room['room_number'] if room else 'N/A',
            'room_type': room['room_type'] if room else 'N/A',
            'guest_name': guest['name'] if guest else 'N/A',
            'guest_email': guest['email'] if guest else 'N/A',
            'guest_phone': guest['phone'] if guest else 'N/A'
        }

class OccupancyModel:
    """Occupancy statistics operations"""

    @staticmethod
    def get_stats() -> Dict:
        """Get current occupancy statistics"""
        try:
            rooms = RoomModel.get_all()
            
            occupied = len([r for r in rooms if r['status'] == 'occupied'])
            available = len([r for r in rooms if r['status'] == 'available'])
            maintenance = len([r for r in rooms if r['status'] == 'maintenance'])
            total = len(rooms)
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            supabase = get_supabase()
            
            # Check-ins today
            check_ins = supabase.table('bookings').select('*').eq('check_in', today).eq('status', 'confirmed').execute()
            
            # Check-outs today
            check_outs = supabase.table('bookings').select('*').eq('check_out', today).eq('status', 'checked_in').execute()
            
            return {
                'total_rooms': total,
                'occupied_rooms': occupied,
                'available_rooms': available,
                'maintenance_rooms': maintenance,
                'occupancy_rate': (occupied / total * 100) if total > 0 else 0,
                'check_ins_today': len(check_ins.data) if hasattr(check_ins, 'data') else 0,
                'check_outs_today': len(check_outs.data) if hasattr(check_outs, 'data') else 0
            }
        except Exception as e:
            logger.error(f"Error getting occupancy stats: {e}")
            # Return default stats
            return {
                'total_rooms': 8,
                'occupied_rooms': 0,
                'available_rooms': 8,
                'maintenance_rooms': 0,
                'occupancy_rate': 0.0,
                'check_ins_today': 0,
                'check_outs_today': 0
            }