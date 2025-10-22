from flask import Blueprint, request, session, jsonify, render_template, current_app
from app.services.checkin_service import verify_and_check_in
from app.services.interaction_service import get_or_create_guest, log_interaction, update_interaction_status
from app.services.housekeeping_service import create_service_request
from llm_handler import llm_classify_intent, llm_answer_faq, summarize_request
from housekeeping_notification import send_housekeeping_notification
import os

chat_bp = Blueprint('chat', __name__)

HOTEL_INFO_PATH = os.path.join(os.path.dirname(__file__), '../../hotel_info.txt')
with open(HOTEL_INFO_PATH, 'r', encoding='utf-8') as f:
    HOTEL_INFO = f.read()

BOOKING_LINK = "https://yourhotelbooking.com"  # Change to your actual portal

def reset_session():
    session.clear()
    session.update({
        'state': 'INIT', 
        'guest_name': None, 
        'guest_phone': None, 
        'checked_in': False,
        'attempt_count': 0,
        'fallback_count': 0
    })

@chat_bp.route('/')
def index():
    reset_session()
    return render_template('index.html')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    state = session.get('state', 'INIT')
    checked_in = session.get('checked_in', False)
    PMS_API_URL = current_app.config['PMS_API_URL']

    # Escape commands
    if not user_message:
        return jsonify({'response': "Please enter a message."})
    if any(x in user_message.lower() for x in ['exit', 'cancel', 'reset', 'start over', 'talk to staff', 'help', 'agent']):
        reset_session()
        return jsonify({'response': "Restarted. I can help with check-in, booking information, hotel FAQs, or housekeeping. What would you like to do?"})

    # Classified intent with improved fallback
    intent = (
        'check_in' if state in ['AWAITING_NAME', 'AWAITING_PHONE']
        else llm_classify_intent(user_message)
    )

    # Already checked-in
    if checked_in and intent == 'check_in':
        room = session.get('checked_in_room', 'your room')
        return jsonify({
            'response': f"You're already checked in to room {room}. I can help with hotel info or housekeeping. What do you need?"
        })

    # --- Check-in logic ---
    if intent == 'check_in' and not checked_in:
        if state == 'INIT':
            session['state'] = 'AWAITING_NAME'
            session['attempt_count'] = 0
            return jsonify({'response': "Welcome! What's the full name on your booking?"})

        elif state == 'AWAITING_NAME':
            # Validate name
            if len(user_message) < 2:
                return jsonify({'response': "Please enter a valid name for your booking."})
            session['guest_name'] = user_message.strip()
            session['state'] = 'AWAITING_PHONE'
            session['attempt_count'] = 0
            return jsonify({'response': f"Thanks, {session['guest_name']}! What's your phone number on the booking?"})

        elif state == 'AWAITING_PHONE':
            guest_phone = user_message.replace('-', '').replace(' ', '').replace('+91', '').replace('(', '').replace(')', '')
            attempt_count = session.get('attempt_count', 0)

            # Validate phone number
            if not guest_phone.isdigit() or len(guest_phone) < 10:
                attempt_count += 1
                session['attempt_count'] = attempt_count
                if attempt_count >= 3:
                    reset_session()
                    return jsonify({
                        'response': "Too many invalid attempts. Let's start over. If you want to book a room, I can share our booking link."
                    })
                return jsonify({'response': f"Please enter a valid 10-digit phone number. Attempt {attempt_count}/3."})

            # Valid phone number, attempt check-in
            guest_id = get_or_create_guest(guest_phone)
            interaction_id = log_interaction(guest_id, intent, user_message)
            result = verify_and_check_in(session['guest_name'], guest_phone, PMS_API_URL)
            if result['success']:
                session.update({
                    'checked_in': True,
                    'checked_in_room': result['room_number'],
                    'guest_phone': guest_phone,
                    'guest_name': result['guest_name'],
                    'state': 'INIT'
                })
                update_interaction_status(interaction_id, "checked_in")
                return jsonify({
                    'response': f"🎉 Welcome {result['guest_name']}!\nYou're checked in to room {result['room_number']} ({result['room_type']}). Key is in Box {result['box_id']}.",
                    'action': {'type': 'unlock', 'box_id': result['box_id'], 'room_number': result['room_number']}
                })
            else:
                update_interaction_status(interaction_id, "failed")
                reset_session()
                # New: If check-in fails, offer booking link and alternatives
                return jsonify({
                    'response': (
                        f"{result['message']}\n\n"
                        f"Don't worry! You can book a room directly at {BOOKING_LINK} — or ask me info about rates, availability, or amenities.\n"
                        "If you'd like to talk to a staff member, just say 'help' or 'agent'."
                    ),
                    'action': {'type': 'alternative', 'next_steps': ['book', 'faq', 'talk to staff']}
                })

    # --- Housekeeping ---
    elif intent == 'housekeeping':
        if not checked_in:
            return jsonify({'response': "Please check in first before making housekeeping requests, or ask about booking."})
        guest_phone = session.get('guest_phone')
        guest_id = get_or_create_guest(guest_phone)
        interaction_id = log_interaction(guest_id, intent, user_message)
        summary = summarize_request(user_message)
        send_housekeeping_notification(user_message, summary, session.get('guest_name'), session.get('checked_in_room'))
        create_service_request(interaction_id, "housekeeping")
        update_interaction_status(interaction_id, "resolved")
        return jsonify({
            'response': (
                f"✅ Housekeeping Request Received for Room {session.get('checked_in_room')}.\n"
                f"{summary}\nOur team will assist you soon. Anything else?"
            ),
            'action': {'type': 'housekeeping', 'summary': summary}
        })

    # --- FAQ and info ---
    elif intent == 'faq' or any(x in user_message.lower() for x in ['book', 'reservation', 'rate', 'price', 'availability']):
        answer = llm_answer_faq(user_message, HOTEL_INFO)
        # When guest asks to book, offer link
        if any(k in user_message.lower() for k in ['book', 'reserve', 'room']):
            answer += f"\nYou can secure a room instantly here: {BOOKING_LINK}"
        # Log for checked-in guests
        if checked_in:
            guest_phone = session.get('guest_phone')
            if guest_phone:
                guest_id = get_or_create_guest(guest_phone)
                interaction_id = log_interaction(guest_id, intent, user_message)
                update_interaction_status(interaction_id, "resolved")
        return jsonify({'response': answer})

    # --- Universal fallback & escalation ---
    fallback = session.get('fallback_count', 0)
    session['fallback_count'] = fallback + 1
    if session['fallback_count'] >= 2:
        reset_session()
        return jsonify({
            'response': (
                "I'm having trouble understanding your request.\n"
                "Would you like to talk to a staff member directly or start over? Type 'help' or 'agent'."
            ),
            'action': {'type': 'escalate'}
        })
    return jsonify({'response': "I can help you with booking, check-in, FAQs, or housekeeping. What would you like to do?"})
