from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import requests
import os
from datetime import datetime
from llm_handler import llm_classify_intent, llm_answer_faq, summarize_request, send_housekeeping_email

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
with open(HOTEL_INFO_PATH, 'r', encoding='utf-8') as f:
    HOTEL_INFO = f.read()

def verify_and_check_in(guest_name, guest_phone):
    """
    Calls the PMS API to find a booking and check the guest in.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        # 1. Get all bookings from the PMS API
        response = requests.get(f"{PMS_API_URL}/bookings")
        if response.status_code != 200:
            return {'success': False, 'message': 'Cannot connect to the booking system.'}
        bookings = response.json().get('data', [])
        # 2. Find a matching, confirmed booking for today
        target_booking = None
        for booking in bookings:
            if (booking['guest_name'].lower() == guest_name.lower() and
                booking['guest_phone'] == guest_phone and
                booking['status'] == 'confirmed' and
                booking['check_in'] == today_str):
                target_booking = booking
                break
        if not target_booking:
            return {'success': False, 'message': "I'm sorry, I couldn't find a booking for today with that name and phone number."}
        # 3. Check in the guest by updating the status via the API
        booking_id = target_booking['booking_id']
        update_response = requests.put(
            f"{PMS_API_URL}/bookings/{booking_id}",
            json={'status': 'checked_in'}
        )
        if update_response.status_code != 200:
            return {'success': False, 'message': 'Found your booking, but there was an error checking you in. Please see the front desk.'}
        # 4. Success!
        room_number = target_booking.get('room_number', 'N/A')
        return {
            'success': True,
            'guest_name': target_booking['guest_name'],
            'room_number': room_number,
            'room_type': target_booking.get('room_type', 'N/A'),
            'box_id': KEY_BOX_MAP.get(room_number, 'Lobby'),
            'booking_id': target_booking['booking_id']
        }
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': 'Error: Cannot connect to the hotel management system. Is it running?'}
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'message': 'An unexpected error occurred.'}

@app.route('/')
def index():
    session.clear()
    session['state'] = 'INIT'
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    state = session.get('state', 'INIT')
    bot_response = "I'm not sure how to help with that. I can help with check-in."
    action = None
    # --- LLM intent classification ---
    intent = llm_classify_intent(user_message.lower())
    # --- Check-in flow ---
    if intent == 'check_in':
        if state == 'INIT':
            bot_response = "Welcome! To check in, I need to find your booking. What's the **full name** on the reservation?"
            session['state'] = 'AWAITING_NAME'
            session['guest_name'] = None
        elif state == 'AWAITING_NAME':
            # Only update guest_name if not already set
            if not session.get('guest_name'):
                session['guest_name'] = user_message.strip()
                bot_response = f"Got it, {session['guest_name']}. And what's the **phone number** associated with the booking?"
                session['state'] = 'AWAITING_PHONE'
            else:
                # If guest_name is already set, prompt for phone number
                bot_response = f"And what's the **phone number** associated with the booking for {session['guest_name']}?"
                session['state'] = 'AWAITING_PHONE'
        elif state == 'AWAITING_PHONE':
            guest_name = session.get('guest_name', '')
            guest_phone = user_message.strip().replace('-', '').replace(' ', '')
            result = verify_and_check_in(guest_name, guest_phone)
            if result['success']:
                bot_response = (
                    f"Perfect, I've found your booking for a **{result['room_type']}** room. Welcome, {result['guest_name']}! "
                    f"You are all checked in. Your key for **Room {result['room_number']}** is in **Box {result['box_id']}**. "
                    "I am unlocking it for you right now. Have a wonderful stay!"
                )
                action = {
                    'type': 'unlock',
                    'box_id': result['box_id'],
                    'room_number': result['room_number']
                }
                session['state'] = 'DONE'
            else:
                bot_response = f"{result['message']} Would you like to try again? (Say 'check in' to restart)"
                session['state'] = 'INIT'
                session['guest_name'] = None
        elif state == 'DONE':
            bot_response = "You are already checked in. If you need further assistance, please see the front desk."
    # --- Housekeeping flow ---
    elif intent == 'housekeeping':
        summary = summarize_request(user_message)
        send_housekeeping_email(summary)
        bot_response = "Your housekeeping request has been received and sent to our staff. Is there anything else I can help with?"
        action = {'type': 'housekeeping', 'summary': summary}
    # --- FAQ/general query flow ---
    elif intent == 'faq':
        answer = llm_answer_faq(user_message, HOTEL_INFO)
        bot_response = answer
    # --- Fallback for other queries ---
    else:
        bot_response = "I'm Nexrova, your AI hotel assistant. I can help with check-in, answer questions, or send requests to staff."
        session['state'] = 'INIT'
    return jsonify({
        'response': bot_response,
        'action': action
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
