# app/services/pms_service.py
import requests
from flask import current_app
from datetime import datetime

def verify_phone_in_pms(phone_number):
    """
    Verify if phone number exists in PMS with upcoming booking or checked-in status
    Returns: dict with booking info or None if not found
    """
    PMS_API_URL = current_app.config['PMS_API_URL']
    clean_phone = phone_number.replace('-', '').replace(' ', '').replace('+91', '')
    
    try:
        response = requests.get(f"{PMS_API_URL}/bookings", timeout=5)
        if response.status_code != 200:
            return None
        
        bookings = response.json().get('data', [])
        
        for booking in bookings:
            booking_phone = booking.get('guest_phone', '').replace('-', '').replace(' ', '').replace('+91', '')
            
            if booking_phone == clean_phone:
                # Check if booking is upcoming (confirmed) or already checked in
                if booking['status'] in ['confirmed', 'checked_in']:
                    return {
                        'found': True,
                        'booking_id': booking['booking_id'],
                        'guest_name': booking.get('guest_name'),
                        'room_number': booking.get('room_number'),
                        'check_in_date': booking.get('check_in'),
                        'check_out_date': booking.get('check_out'),
                        'status': booking['status']
                    }
        
        return None
        
    except Exception as e:
        print(f"Error verifying phone in PMS: {e}")
        return None

def verify_and_check_in(guest_name, guest_phone):
    """Check-in guest through PMS API"""
    PMS_API_URL = current_app.config['PMS_API_URL']
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        response = requests.get(f"{PMS_API_URL}/bookings", timeout=5)
        if response.status_code != 200:
            return {'success': False, 'message': 'Cannot connect to the booking system.'}
        
        bookings = response.json().get('data', [])
        target_booking = None
        
        for booking in bookings:
            booking_phone = booking.get('guest_phone', '').replace('-', '').replace(' ', '').replace('+91', '')
            input_phone = guest_phone.replace('-', '').replace(' ', '').replace('+91', '')
            
            if (booking['guest_name'].lower() == guest_name.lower() and
                    booking_phone == input_phone and
                    booking['status'] == 'confirmed' and
                    booking['check_in'] == today_str):
                target_booking = booking
                break
        
        if not target_booking:
            return {
                'success': False,
                'message': "I'm sorry, I couldn't find a confirmed booking for today with that name and phone number. Please check your details or contact the front desk."
            }
        
        booking_id = target_booking['booking_id']
        update_response = requests.put(
            f"{PMS_API_URL}/bookings/{booking_id}",
            json={'status': 'checked_in'},
            timeout=5
        )
        
        if update_response.status_code != 200:
            return {
                'success': False,
                'message': 'Found your booking, but there was an error checking you in. Please see the front desk.'
            }
        
        updated_data = update_response.json().get('data', {})
        room_number = updated_data.get('room_number', target_booking.get('room_number', 'N/A'))
        room_type = updated_data.get('room_type', target_booking.get('room_type', 'N/A'))
        
        return {
            'success': True,
            'guest_name': updated_data.get('guest_name', target_booking['guest_name']),
            'room_number': room_number,
            'room_type': room_type,
            'box_id': current_app.config['KEY_BOX_MAP'].get(str(room_number), 'Lobby'),
            'booking_id': booking_id
        }
        
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': 'Error: Cannot connect to the hotel management system. Please contact the front desk.'}
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Error: Request timed out. Please try again or contact the front desk.'}
    except Exception as e:
        print(f"Error in verify_and_check_in: {e}")
        return {'success': False, 'message': 'An unexpected error occurred. Please contact the front desk.'}
