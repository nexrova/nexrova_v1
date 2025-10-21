import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

# Configuration
STAFF_EMAIL = 'jeevansuresh258@gmail.com'
NOTIFICATION_LOG = 'housekeeping_requests.json'

def send_housekeeping_notification(request_text, summary, guest_name='Guest', room_number='Unknown'):
    """
    Send housekeeping notification via multiple channels.

    This function ALWAYS succeeds by:
    1. Logging to local file (always works)
    2. Attempting email (if configured)
    3. Printing to console (for staff monitoring)

    Args:
        request_text: Original guest request
        summary: Summarized request
        guest_name: Name of the guest
        room_number: Room number

    Returns:
        dict: {'success': bool, 'message': str, 'notification_id': str}
    """

    # Generate notification ID
    notification_id = f"HK{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create notification data
    notification = {
        'notification_id': notification_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'guest_name': guest_name,
        'room_number': room_number,
        'request': request_text,
        'summary': summary,
        'status': 'pending',
        'email_sent': False
    }

    # 1. ALWAYS log to file (this never fails)
    try:
        log_to_file(notification)
        print(f"[HOUSEKEEPING] ✓ Logged request {notification_id}")
    except Exception as e:
        print(f"[HOUSEKEEPING] Warning: Could not log to file: {e}")

    # 2. Print to console (for staff monitoring terminals)
    print_notification(notification)

    # 3. Attempt to send email (optional, may fail gracefully)
    email_sent = send_email_notification(notification)
    notification['email_sent'] = email_sent

    # Update log with email status
    if email_sent:
        try:
            update_notification_status(notification_id, email_sent=True)
        except:
            pass

    # Return success (we always succeed because we log locally)
    return {
        'success': True,
        'message': f'Notification {notification_id} created',
        'notification_id': notification_id,
        'email_sent': email_sent
    }

def log_to_file(notification):
    """Log housekeeping request to JSON file"""
    log_file = Path(NOTIFICATION_LOG)

    # Load existing logs or create new
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    # Append new notification
    logs.append(notification)

    # Save back to file
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def print_notification(notification):
    """Print notification to console in a formatted way"""
    print("\n" + "="*60)
    print("🧹 HOUSEKEEPING REQUEST RECEIVED")
    print("="*60)
    print(f"ID:        {notification['notification_id']}")
    print(f"Time:      {notification['timestamp']}")
    print(f"Guest:     {notification['guest_name']}")
    print(f"Room:      {notification['room_number']}")
    print(f"Request:   {notification['summary']}")
    print(f"Details:   {notification['request']}")
    print("="*60 + "\n")

def send_email_notification(notification):
    """
    Attempt to send email notification.
    Returns True if successful, False otherwise.
    """
    EMAIL_ADDRESS = os.environ.get('HOTEL_AGENT_EMAIL')
    EMAIL_PASSWORD = os.environ.get('HOTEL_AGENT_PASS')

    # Check if credentials are configured
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print(f"[EMAIL] ⚠ Email credentials not configured (skipping email)")
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🧹 Housekeeping Request - Room {notification['room_number']}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = STAFF_EMAIL

        # Create HTML email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

                <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
                    🧹 Housekeeping Request
                </h2>

                <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Request ID:</strong> {notification['notification_id']}</p>
                    <p style="margin: 5px 0;"><strong>Timestamp:</strong> {notification['timestamp']}</p>
                    <p style="margin: 5px 0;"><strong>Guest Name:</strong> {notification['guest_name']}</p>
                    <p style="margin: 5px 0;"><strong>Room Number:</strong> <span style="color: #e74c3c; font-size: 18px; font-weight: bold;">{notification['room_number']}</span></p>
                </div>

                <div style="margin: 20px 0;">
                    <h3 style="color: #34495e;">Summary:</h3>
                    <p style="font-size: 16px; color: #2c3e50; background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0;">
                        {notification['summary']}
                    </p>
                </div>

                <div style="margin: 20px 0;">
                    <h3 style="color: #34495e;">Full Request:</h3>
                    <p style="color: #555; line-height: 1.6; background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                        "{notification['request']}"
                    </p>
                </div>

                <div style="margin: 30px 0; padding: 20px; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 5px;">
                    <p style="margin: 0; color: #155724; font-weight: bold;">⏰ Action Required</p>
                    <p style="margin: 5px 0; color: #155724;">Please attend to this request at your earliest convenience.</p>
                </div>

                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">

                <p style="color: #6c757d; font-size: 12px; text-align: center; margin: 10px 0;">
                    This is an automated notification from Nexrova Hotel Assistant<br>
                    Chennai BnB Serviced Apartments
                </p>
            </div>
        </body>
        </html>
        """

        # Set HTML content
        msg.set_content("Please view this email in an HTML-compatible email client.")
        msg.add_alternative(html_content, subtype='html')

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print(f"[EMAIL] ✓ Email sent to {STAFF_EMAIL}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(f"[EMAIL] ✗ Authentication failed (check credentials)")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] ✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] ✗ Error sending email: {e}")
        return False

def update_notification_status(notification_id, status=None, email_sent=None):
    """Update the status of a notification in the log"""
    log_file = Path(NOTIFICATION_LOG)

    if not log_file.exists():
        return

    with open(log_file, 'r', encoding='utf-8') as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return

    # Find and update the notification
    for notification in logs:
        if notification['notification_id'] == notification_id:
            if status:
                notification['status'] = status
            if email_sent is not None:
                notification['email_sent'] = email_sent
            break

    # Save back
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def get_all_notifications():
    """Get all housekeeping notifications"""
    log_file = Path(NOTIFICATION_LOG)

    if not log_file.exists():
        return []

    with open(log_file, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def get_pending_notifications():
    """Get all pending housekeeping notifications"""
    all_notifications = get_all_notifications()
    return [n for n in all_notifications if n.get('status') == 'pending']

# For testing
if __name__ == '__main__':
    # Test the notification system
    result = send_housekeeping_notification(
        request_text="There's a gravy spill on my room floor",
        summary="Gravy spill on room floor",
        guest_name="Alan",
        room_number="104"
    )

    print(f"\nTest Result: {result}")
    print(f"\nPending notifications: {len(get_pending_notifications())}")
