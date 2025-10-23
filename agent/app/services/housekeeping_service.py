# app/services/housekeeping_service.py
import os
from housekeeping_notification import send_housekeeping_notification

def process_housekeeping_request(user_message, guest_name, room_number, summary):
    """Process a housekeeping request and send notification"""
    try:
        send_result = send_housekeeping_notification(
            request_text=user_message,
            summary=summary,
            guest_name=guest_name,
            room_number=room_number
        )
        return send_result
    except Exception as e:
        print(f"Error sending housekeeping notification: {e}")
        return {'success': False, 'message': str(e)}
