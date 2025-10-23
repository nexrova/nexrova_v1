# app/models/service_request_model.py
from app.models.supabase_client import get_supabase_client
from datetime import datetime

def create_service_request(interaction_id, service_type, staff_id=None):
    """Create a new service request"""
    supabase = get_supabase_client()
    now = datetime.now().isoformat()
    
    request_data = {
        'interaction_id': interaction_id,
        'service_type': service_type,
        'request_time': now
    }
    
    if staff_id:
        request_data['staff_id'] = staff_id
    
    result = supabase.table('ServiceRequests').insert(request_data).execute()
    return result.data[0] if result.data else None

def update_service_request(request_id, updates):
    """Update service request details"""
    supabase = get_supabase_client()
    supabase.table('ServiceRequests').update(updates).eq('request_id', request_id).execute()

def get_service_requests_by_interaction(interaction_id):
    """Get all service requests for an interaction"""
    supabase = get_supabase_client()
    result = supabase.table('ServiceRequests').select('*').eq('interaction_id', interaction_id).execute()
    return result.data if result.data else []
