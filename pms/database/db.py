"""
Database connection and Supabase client initialization
"""
from supabase import create_client, Client
from config import Config

class Database:
    """Supabase database client singleton"""
    _client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance
        Returns:
            Client: Supabase client instance
        """
        if cls._client is None:
            Config.validate()
            cls._client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY
            )
        return cls._client

    @classmethod
    def reset_client(cls):
        """Reset the client instance (useful for testing)"""
        cls._client = None

# Convenience function to get the client

def get_supabase() -> Client:
    """
    Get Supabase client instance
    Returns:
        Client: Supabase client instance
    """
    return Database.get_client()