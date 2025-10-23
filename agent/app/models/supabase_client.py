# app/models/supabase_client.py
from supabase import create_client, Client
from flask import current_app

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_KEY']
    )
