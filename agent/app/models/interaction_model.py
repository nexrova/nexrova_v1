# app/models/interaction_model.py
from app.models.supabase_client import get_supabase_client
from datetime import datetime

def log_interaction(guest_id, intent_type, user_query, status="initiated"):
    """Log a new interaction"""
    supabase = get_supabase_client()
    timestamp = datetime.now().isoformat()
    interaction = supabase.table('Interactions').insert({
        'guest_id': guest_id,
        'timestamp': timestamp,
        'intent_type': intent_type,
        'user_query': user_query,
        'status': status,
        'phone_number': None  # Will be updated if needed
    }).execute()
    return interaction.data[0]['interaction_id'] if interaction.data else None

def update_interaction_status(interaction_id, new_status):
    """Update interaction status"""
    supabase = get_supabase_client()
    supabase.table('Interactions').update({'status': new_status}).eq('interaction_id', interaction_id).execute()

def get_interactions_by_guest(guest_id, limit=10):
    """Get recent interactions for a guest"""
    supabase = get_supabase_client()
    result = supabase.table('Interactions').select('*').eq('guest_id', guest_id).order('timestamp', desc=True).limit(limit).execute()
    return result.data if result.data else []

def store_conversation(guest_id, phone_number, conversation_data):
    """Store entire conversation as a record"""
    supabase = get_supabase_client()
    timestamp = datetime.now().isoformat()
    
    # Store conversation summary
    conversation_summary = {
        'guest_id': guest_id,
        'phone_number': phone_number,
        'timestamp': timestamp,
        'total_messages': len(conversation_data),
        'conversation_data': conversation_data
    }
    
    # You can create a separate Conversations table or store in Interactions
    # For now, we'll mark all interactions as part of a conversation session
    for interaction in conversation_data:
        log_interaction(
            guest_id=guest_id,
            intent_type=interaction.get('intent', 'other'),
            user_query=interaction.get('user_message', ''),
            status='completed'
        )
