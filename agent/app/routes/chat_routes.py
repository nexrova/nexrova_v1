# app/routes/chat_routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.models.guest_model import get_or_create_guest, update_guest_on_checkin
from app.models.interaction_model import log_interaction, update_interaction_status
from app.models.service_request_model import create_service_request
from app.services.pms_service import verify_and_check_in
from app.services.housekeeping_service import process_housekeeping_request
from llm_handler import llm_classify_intent, llm_answer_faq, summarize_request
import os

chat_bp = Blueprint('chat', __name__)

# Load hotel info
HOTEL_INFO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'hotel_info.txt')
try:
    with open(HOTEL_INFO_PATH, 'r', encoding='utf-8') as f:
        HOTEL_INFO = f.read()
except FileNotFoundError:
    HOTEL_INFO = "Hotel information not available."

@chat_bp.route('/chat')
def index():
    """Render chat page - requires login"""
    if 'guest_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('index.html')

@chat_bp.route('/chat/message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    # Check if user is logged in
    if 'guest_id' not in session:
        return jsonify({
            'response': 'Session expired. Please log in again.',
            'action': {'type': 'redirect', 'url': url_for('auth.login')}
        })
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': "Please enter a message.", 'action': None})
    
    # Get session data
    guest_id = session.get('guest_id')
    state = session.get('state', 'INIT')
    checked_in = session.get('checked_in', False)
    guest_name = session.get('guest_name', 'Guest')
    guest_phone = session.get('phone_number')
    room_number = session.get('checked_in_room', None)
    
    bot_response = "I'm not sure how to help with that."
    action = None
    
    # Store conversation
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    conversation_entry = {
        'user_message': user_message,
        'timestamp': None
    }
    
    # Already checked-in shortcut
    if checked_in and any(word in user_message.lower() for word in ['check in', 'checked in', 'already']):
        room = session.get('checked_in_room', 'your room')
        bot_response = (
            f"You're already checked in to Room {room}! \n\n"
            "I can help you with:\n"
            "• **Questions** about the hotel\n"
            "• **Housekeeping** requests\n\n"
            "How else can I assist you?"
        )
        conversation_entry['bot_response'] = bot_response
        conversation_entry['intent'] = 'other'
        session['conversation_history'].append(conversation_entry)
        return jsonify({'response': bot_response, 'action': None})
    
    # Intent classification
    if state in ['AWAITING_NAME', 'AWAITING_PHONE']:
        intent = 'check_in'
    else:
        intent = llm_classify_intent(user_message.lower())
    
    conversation_entry['intent'] = intent
    
    # --- Check-in Flow ---
    if state == 'AWAITING_NAME':
        session['guest_name'] = user_message.strip()
        bot_response = f"Got it, {session['guest_name']}. And what's the **phone number** associated with the booking?"
        session['state'] = 'AWAITING_PHONE'
        
    elif state == 'AWAITING_PHONE':
        guest_name = session.get('guest_name', '')
        guest_phone_input = user_message.strip().replace('-', '').replace(' ', '')
        
        if not guest_name:
            bot_response = "I seem to have lost your name. Let's start over. What's the full name on the reservation?"
            session['state'] = 'AWAITING_NAME'
            session['guest_name'] = None
        elif not guest_phone_input.isdigit():
            bot_response = "Please enter a valid phone number (digits only)."
            session['state'] = 'AWAITING_PHONE'
        else:
            try:
                interaction_id = log_interaction(guest_id, intent, user_message, "initiated")
                result = verify_and_check_in(guest_name, guest_phone_input)
                
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
                    
                    # Update database
                    update_guest_on_checkin(
                        guest_id, 
                        result["guest_name"], 
                        result["room_number"], 
                        result.get('check_in_date')
                    )
                    update_interaction_status(interaction_id, "checked_in")
                    
                    # Update session
                    session['state'] = 'INIT'
                    session['checked_in'] = True
                    session['checked_in_room'] = result['room_number']
                    session['guest_name'] = result['guest_name']
                else:
                    bot_response = (
                        f"{result['message']} \n\n"
                        "Would you like to try again? (Say 'check in' to restart, or ask a question)"
                    )
                    update_interaction_status(interaction_id, "failed")
                    session['state'] = 'INIT'
                    session['guest_name'] = None
            except Exception as e:
                bot_response = f"Sorry, there was an error processing your check-in: {e}"
                
    elif intent == 'check_in' and state == 'INIT' and not checked_in:
        bot_response = "Welcome! To check you in, I need to verify your booking. What's the **full name** on the reservation?"
        session['state'] = 'AWAITING_NAME'
        session['guest_name'] = None
        
    # --- Housekeeping Flow ---
    elif intent == 'housekeeping' and checked_in:
        try:
            interaction_id = log_interaction(guest_id, intent, user_message, "initiated")
            summary = summarize_request(user_message)
            
            send_result = process_housekeeping_request(
                user_message, guest_name, room_number, summary
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
            
            # Log service request
            create_service_request(interaction_id, "housekeeping")
            update_interaction_status(interaction_id, "resolved")
            
        except Exception as e:
            bot_response = f"Sorry, there was an error processing your housekeeping request: {e}"
            
        session['state'] = 'INIT'
        
    # --- FAQ/General Query ---
    elif intent == 'faq':
        answer = llm_answer_faq(user_message, HOTEL_INFO)
        
        try:
            interaction_id = log_interaction(guest_id, intent, user_message, "initiated")
            update_interaction_status(interaction_id, "resolved")
        except:
            pass
        
        bot_response = answer
        session['state'] = 'INIT'
        
    # --- Fallback ---
    else:
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
    
    # Store conversation
    conversation_entry['bot_response'] = bot_response
    session['conversation_history'].append(conversation_entry)
    session.modified = True
    
    return jsonify({'response': bot_response, 'action': action})

@chat_bp.route('/chat/reset', methods=['POST'])
def reset():
    """Reset conversation"""
    session['state'] = 'INIT'
    session['conversation_history'] = []
    return jsonify({'response': "Conversation reset. How can I help you?", 'action': None})
