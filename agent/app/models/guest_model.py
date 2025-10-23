# app/models/guest_model.py
from app.models.supabase_client import get_supabase_client
from datetime import datetime

def get_guest_by_phone(phone_number):
    """Get guest record by phone number"""
    supabase = get_supabase_client()
    result = supabase.table('Guest').select('*').eq('phone_number', phone_number).execute()
    return result.data[0] if result.data else None

def create_guest(phone_number):
    """Create a new guest record"""
    supabase = get_supabase_client()
    result = supabase.table('Guest').insert({'phone_number': int(phone_number)}).execute()
    return result.data[0] if result.data else None

def get_or_create_guest(phone_number):
    """Get existing guest or create new one"""
    if not phone_number or not phone_number.isdigit():
        raise ValueError("Invalid or missing phone number for guest record.")
    
    guest = get_guest_by_phone(phone_number)
    if guest:
        return guest['guest_id'], False
    
    new_guest = create_guest(phone_number)
    return new_guest['guest_id'], True

def update_guest_on_checkin(guest_id, name, room_number, check_in_date, pms_id=None):
    """Update guest information after check-in"""
    supabase = get_supabase_client()
    update_data = {
        'name': name,
        'room_number': room_number,
        'check_in_date': check_in_date
    }
    if pms_id:
        update_data['pms_id'] = pms_id
    
    supabase.table('Guest').update(update_data).eq('guest_id', guest_id).execute()

def get_guest_by_id(guest_id):
    """Get guest by ID"""
    supabase = get_supabase_client()
    result = supabase.table('Guest').select('*').eq('guest_id', guest_id).execute()
    return result.data[0] if result.data else None
