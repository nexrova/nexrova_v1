from app.models.supabase_client import supabase
from datetime import datetime

def create_service_request(interaction_id, service_type):
    supabase.table('ServiceRequests').insert({
        'interaction_id': interaction_id,
        'service_type': service_type,
        'request_time': datetime.now().isoformat()
    }).execute()
