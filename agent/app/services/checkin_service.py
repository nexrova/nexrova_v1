import requests
from datetime import datetime

KEY_BOX_MAP = {
    '101': 'A1', '102': 'A2', '103': 'A3', '104': 'A4',
    '105': 'B1', '106': 'B2', '107': 'B3', '108': 'B4',
}

def verify_and_check_in(guest_name, guest_phone, PMS_API_URL):
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        resp = requests.get(f"{PMS_API_URL}/bookings", timeout=5)
        resp.raise_for_status()
        bookings = resp.json().get('data', [])
        normalized_phone = guest_phone.replace('-', '').replace(' ', '').replace('+91', '')

        for booking in bookings:
            if (booking.get('guest_name', '').lower() == guest_name.lower() and
                    booking.get('guest_phone', '').replace('+91', '').replace(' ', '').replace('-', '') == normalized_phone and
                    booking.get('check_in') == today and
                    booking.get('status') == 'confirmed'):
                # Found valid booking
                update = requests.put(
                    f"{PMS_API_URL}/bookings/{booking['booking_id']}",
                    json={'status': 'checked_in'},
                    timeout=5
                )
                update.raise_for_status()
                updated = update.json().get('data', {})
                return {
                    'success': True,
                    'guest_name': updated.get('guest_name', guest_name),
                    'room_number': updated.get('room_number'),
                    'room_type': updated.get('room_type'),
                    'box_id': KEY_BOX_MAP.get(str(updated.get('room_number')), 'Lobby')
                }
        return {'success': False, 'message': 'Booking not found for today'}
    except requests.RequestException as e:
        print(f"PMS error: {str(e)}")
        return {'success': False, 'message': 'Service unavailable, please contact front desk'}
