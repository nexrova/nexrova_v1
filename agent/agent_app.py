from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import requests
import os
from datetime import datetime
from llm_handler import llm_classify_intent, llm_answer_faq, summarize_request
from housekeeping_notification import send_housekeeping_notification

# Configure Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-nexrova'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# PMS API URL (should match the PMS backend)
PMS_API_URL = "http://127.0.0.1:5000/api"

# Key box mapping
KEY_BOX_MAP = {
    '101': 'A1', '102': 'A2', '103': 'A3', '104': 'A4',
    '105': 'B1', '106': 'B2', '107': 'B3', '108': 'B4',
}

# Load hotel info for FAQ
HOTEL_INFO_PATH = os.path.join(os.path.dirname(__file__), 'hotel_info.txt')
try:
    with open(HOTEL_INFO_PATH, 'r', encoding='utf-8') as f:
        HOTEL_INFO = f.read()
except FileNotFoundError:
    HOTEL_INFO = "Hotel information not available."
    print(f"Warning: {HOTEL_INFO_PATH} not found")

def verify_and_check_in(guest_name, guest_phone):
    """
    Calls the PMS API to find a booking and check the guest in.

    FIXED: Now properly searches for 'confirmed' bookings and updates them to 'checked_in'
    """
    today_str = datetime.now().strftime('%Y-%m-%d')

    try:
        # 1. Get all bookings from the PMS API
        response = requests.get(f"{PMS_API_URL}/bookings", timeout=5)
        if response.status_code != 200:
            return {'success': False, 'message': 'Cannot connect to the booking system.'}

        bookings = response.json().get('data', [])

        # 2. Find a matching, confirmed booking for today
        target_booking = None
        for booking in bookings:
            # Normalize phone number for comparison
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

        # 3. Check in the guest by updating the status via the API
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

        # 4. Get updated booking with room details
        updated_data = update_response.json().get('data', {})

        # 5. Success! Extract room information
        room_number = updated_data.get('room_number', target_booking.get('room_number', 'N/A'))
        room_type = updated_data.get('room_type', target_booking.get('room_type', 'N/A'))

        return {
            'success': True,
            'guest_name': updated_data.get('guest_name', target_booking['guest_name']),
            'room_number': room_number,
            'room_type': room_type,
            'box_id': KEY_BOX_MAP.get(str(room_number), 'Lobby'),
            'booking_id': booking_id
        }

    except requests.exceptions.ConnectionError:
        return {
            'success': False, 
            'message': 'Error: Cannot connect to the hotel management system. Please contact the front desk.'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Error: Request timed out. Please try again or contact the front desk.'
        }
    except Exception as e:
        print(f"Error in verify_and_check_in: {e}")
        return {
            'success': False, 
            'message': 'An unexpected error occurred. Please contact the front desk.'
        }

@app.route('/')
def index():
    # Initialize session state
    session.clear()
    session['state'] = 'INIT'
    session['guest_name'] = None
    session['checked_in'] = False
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({
            'response': "Please enter a message.",
            'action': None
        })

    state = session.get('state', 'INIT')
    checked_in = session.get('checked_in', False)
    guest_name = session.get('guest_name', None)
    room_number = session.get('checked_in_room', None)
    bot_response = "I'm not sure how to help with that."
    action = None

    # ============================================================
    # FIXED: Handle already checked-in guests differently
    # ============================================================

    # If user is already checked in and says something about check-in
    if checked_in and any(word in user_message.lower() for word in ['check in', 'checked in', 'already']):
        room = session.get('checked_in_room', 'your room')
        bot_response = (
            f"You're already checked in to Room {room}! \n\n"
            "I can help you with:\n"
            "• **Questions** about the hotel\n"
            "• **Housekeeping** requests\n\n"
            "How else can I assist you?"
        )
        return jsonify({
            'response': bot_response,
            'action': None
        })

    # ============================================================
    # FIXED: Only classify intent if NOT in middle of check-in
    # ============================================================

    if state in ['AWAITING_NAME', 'AWAITING_PHONE']:
        # Don't classify intent, we're collecting check-in data
        intent = 'check_in'
    else:
        # Classify intent for new interactions
        intent = llm_classify_intent(user_message.lower())

    # ============================================================
    # Check-in flow
    # ============================================================

    if state == 'AWAITING_NAME':
        # Collecting name
        session['guest_name'] = user_message.strip()
        bot_response = f"Got it, {session['guest_name']}. And what's the **phone number** associated with the booking?"
        session['state'] = 'AWAITING_PHONE'

    elif state == 'AWAITING_PHONE':
        # Collecting phone and attempting check-in
        guest_name = session.get('guest_name', '')
        guest_phone = user_message.strip().replace('-', '').replace(' ', '')

        if not guest_name:
            bot_response = "I seem to have lost your name. Let's start over. What's the full name on the reservation?"
            session['state'] = 'AWAITING_NAME'
            session['guest_name'] = None
        else:
            # Attempt to verify and check in
            result = verify_and_check_in(guest_name, guest_phone)

            if result['success']:
                bot_response = (
                    f"Perfect! Welcome, {result['guest_name']}! \n\n"
                    f"You are all checked in to your **{result['room_type']}** room. \n"
                    f"Your room number is **{result['room_number']}**. \n\n"
                    f"Your key is in **Box {result['box_id']}**. I am unlocking it for you right now. \n\n"
                    "Have a wonderful stay! 🎉\n\n"
                    "I'm here if you need anything else - just ask!"
                )
                action = {
                    'type': 'unlock',
                    'box_id': result['box_id'],
                    'room_number': result['room_number']
                }
                # FIXED: Mark as checked in and reset to INIT
                session['state'] = 'INIT'
                session['checked_in'] = True
                session['checked_in_room'] = result['room_number']
                session['guest_name'] = result['guest_name']
            else:
                bot_response = (
                    f"{result['message']} \n\n"
                    "Would you like to try again? (Say 'check in' to restart, or ask a question)"
                )
                session['state'] = 'INIT'
                session['guest_name'] = None

    # ============================================================
    # Start new check-in
    # ============================================================

    elif intent == 'check_in' and state == 'INIT' and not checked_in:
        # Start check-in flow
        bot_response = "Welcome! To check you in, I need to verify your booking. What's the **full name** on the reservation?"
        session['state'] = 'AWAITING_NAME'
        session['guest_name'] = None

    # ============================================================
    # FIXED: Housekeeping flow with proper notification
    # ============================================================

    elif intent == 'housekeeping':
        # Get guest context
        guest_name = session.get('guest_name', 'Guest')
        room_number = session.get('checked_in_room', 'Unknown')

        # Summarize the request
        summary = summarize_request(user_message)

        # Send notification (ALWAYS works, no email dependency)
        send_result = send_housekeeping_notification(
            request_text=user_message,
            summary=summary,
            guest_name=guest_name,
            room_number=room_number
        )

        if send_result['success']:
            bot_response = (
                f"✅ Your housekeeping request has been received!\n\n"
                f"**Request:** {summary}\n"
                f"**Room:** {room_number}\n\n"
                "Our staff has been notified and will attend to it shortly.\n\n"
                "Is there anything else I can help with?"
            )
            action = {
                'type': 'housekeeping', 
                'summary': summary,
                'notification_id': send_result.get('notification_id')
            }
        else:
            # Even if email fails, log it locally
            bot_response = (
                f"✅ Your housekeeping request has been logged!\n\n"
                f"**Request:** {summary}\n"
                f"**Room:** {room_number}\n\n"
                "Our staff will be notified. For urgent requests, please call the front desk.\n\n"
                "Is there anything else I can help with?"
            )
            action = {
                'type': 'housekeeping',
                'summary': summary
            }

        # Stay in INIT state
        session['state'] = 'INIT'

    # ============================================================
    # FAQ/general query flow
    # ============================================================

    elif intent == 'faq':
        answer = llm_answer_faq(user_message, HOTEL_INFO)
        bot_response = answer
        # Stay in INIT state
        session['state'] = 'INIT'

    # ============================================================
    # Fallback for other queries
    # ============================================================

    else:
        # Check if already checked in
        if checked_in:
            bot_response = (
                "I can help you with:\n\n"
                "• **Questions** - Ask about hotel amenities, location, or services\n"
                "• **Housekeeping** - Send requests to our staff\n\n"
                "What would you like to know?"
            )
        else:
            bot_response = (
                "I'm Nexrova, your AI hotel assistant. I can help with:\n\n"
                "• **Check-in** - Verify your booking and get your room key\n"
                "• **Questions** - Ask about hotel amenities, location, or services\n"
                "• **Housekeeping** - Send requests to our staff\n\n"
                "How can I assist you today?"
            )
        session['state'] = 'INIT'

    return jsonify({
        'response': bot_response,
        'action': action
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the conversation state"""
    session.clear()
    session['state'] = 'INIT'
    session['guest_name'] = None
    session['checked_in'] = False
    return jsonify({
        'response': "Conversation reset. How can I help you?",
        'action': None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
