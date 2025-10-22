from datetime import datetime
from app.models.supabase_client import supabase

def get_or_create_guest(phone_number):
    if not phone_number or not phone_number.isdigit():
        raise ValueError("Invalid phone number")
    result = supabase.table('Guest').select('*').eq('phone_number', phone_number).execute()
    if result.data:
        return result.data[0]['guest_id']
    inserted = supabase.table('Guest').insert({'phone_number': int(phone_number)}).execute()
    return inserted.data[0]['guest_id']

def log_interaction(guest_id, intent_type, query, status="initiated"):
    data = {
        'guest_id': guest_id,
        'timestamp': datetime.now().isoformat(),
        'intent_type': intent_type,
        'user_query': query,
        'status': status
    }
    return supabase.table('Interactions').insert(data).execute().data[0]['interaction_id']

def update_interaction_status(interaction_id, new_status):
    supabase.table('Interactions').update({'status': new_status}).eq('interaction_id', interaction_id).execute()
