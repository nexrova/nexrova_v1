# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.services.pms_service import verify_phone_in_pms
from app.models.guest_model import get_or_create_guest, update_guest_on_checkin

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    """Render login page"""
    session.clear()
    return render_template('login.html')

@auth_bp.route('/verify_phone', methods=['POST'])
def verify_phone():
    """Verify phone number and check PMS for booking"""
    data = request.get_json()
    phone_number = data.get('phone_number', '').strip()
    
    if not phone_number:
        return jsonify({
            'success': False,
            'message': 'Please enter a valid phone number.'
        })
    
    # Clean phone number
    clean_phone = phone_number.replace('-', '').replace(' ', '').replace('+91', '')
    
    if not clean_phone.isdigit() or len(clean_phone) != 10:
        return jsonify({
            'success': False,
            'message': 'Please enter a valid 10-digit phone number.'
        })
    
    # Check if phone exists in PMS
    pms_booking = verify_phone_in_pms(clean_phone)
    
    if not pms_booking:
        return jsonify({
            'success': False,
            'message': 'No booking found with this phone number. Please contact the front desk.'
        })
    
    # Create or get guest in Supabase
    try:
        guest_id, is_new = get_or_create_guest(clean_phone)
        
        # Update guest info if booking exists
        if pms_booking['status'] == 'checked_in':
            update_guest_on_checkin(
                guest_id=guest_id,
                name=pms_booking['guest_name'],
                room_number=pms_booking['room_number'],
                check_in_date=pms_booking['check_in_date'],
                pms_id=pms_booking['booking_id']
            )
        
        # Store in session
        session['guest_id'] = guest_id
        session['phone_number'] = clean_phone
        session['guest_name'] = pms_booking['guest_name']
        session['pms_booking'] = pms_booking
        session['state'] = 'INIT'
        session['checked_in'] = (pms_booking['status'] == 'checked_in')
        session['conversation_history'] = []
        
        if pms_booking['status'] == 'checked_in':
            session['checked_in_room'] = pms_booking['room_number']
        
        return jsonify({
            'success': True,
            'message': f"Welcome{', ' + pms_booking['guest_name'] if pms_booking['guest_name'] else ''}!",
            'booking_status': pms_booking['status'],
            'redirect': url_for('chat.index')
        })
        
    except Exception as e:
        print(f"Error in verify_phone: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """End conversation and store in database"""
    # Store conversation history before clearing
    if 'conversation_history' in session and 'guest_id' in session:
        # Conversation is already logged via interactions
        pass
    
    session.clear()
    return jsonify({'success': True, 'redirect': url_for('auth.login')})
