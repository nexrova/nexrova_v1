import requests
import os
from datetime import datetime

# Ollama API Configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral')

def call_ollama(prompt, model=OLLAMA_MODEL, max_tokens=500):
    """Call Ollama API with improved error handling"""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3,  # Lower temperature for more consistent responses
                    "top_p": 0.9
                }
            },
            timeout=15  # Increased timeout
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            print(f"Ollama API error: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("Warning: Cannot connect to Ollama. Using fallback logic.")
        return None
    except requests.exceptions.Timeout:
        print("Warning: Ollama request timed out. Using fallback logic.")
        return None
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def llm_classify_intent(user_message):
    """
    Improved intent classification with better logic and fallbacks
    """
    user_lower = user_message.lower().strip()
    
    # Handle very short messages
    if len(user_message) < 2:
        return 'other'
    
    prompt = f"""You are a hotel chatbot. Classify this guest message into exactly ONE category:

check_in: Guest wants to START the check-in process (not already checked in)
housekeeping: Guest needs cleaning, towels, maintenance, room service, or reports issues/spills
faq: Guest is asking questions about hotel facilities, location, amenities, directions, timing
other: Everything else including greetings, thanks, complaints, already checked in

Message: "{user_message}"

Rules:
- If they say they're already checked in -> other
- If asking about room cleaning/issues -> housekeeping  
- If asking what/where/when/how about hotel -> faq
- Only "check_in" if they want to START checking in

Respond with only ONE word:"""

    # Try LLM first
    llm_response = call_ollama(prompt, max_tokens=20)
    
    if llm_response:
        response_clean = llm_response.lower().strip()
        # Extract intent from response
        for intent in ['check_in', 'housekeeping', 'faq', 'other']:
            if intent in response_clean:
                return intent

    # Enhanced fallback keyword matching
    
    # Check-in: Only if explicitly starting check-in process
    checkin_phrases = [
        'check in', 'check-in', 'checkin',
        'i want to check in', 'need to check in', 'check me in',
        'start check in', 'begin check in'
    ]
    
    # Don't classify as check-in if already checked in
    already_checked = any(phrase in user_lower for phrase in [
        'already checked', 'already check', "i'm checked", 'checked in already'
    ])
    
    if not already_checked and any(phrase in user_lower for phrase in checkin_phrases):
        return 'check_in'

    # Housekeeping: Expanded to catch more scenarios
    housekeeping_keywords = [
        # Basic cleaning
        'clean', 'housekeeping', 'maid', 'room service',
        # Items/amenities
        'towel', 'toilet paper', 'tissue', 'soap', 'shampoo', 'amenities',
        'pillow', 'blanket', 'sheet', 'linen',
        # Issues/problems
        'spill', 'spilled', 'dirty', 'mess', 'stain', 'wet', 'sticky',
        'broken', 'not working', 'fix', 'repair', 'maintenance',
        # Food/drink related
        'gravy', 'coffee', 'water', 'juice', 'food', 'drink', 'wine',
        # Room equipment
        'ac', 'air conditioning', 'heater', 'light', 'bulb', 'tv', 'remote',
        'door', 'lock', 'key', 'card', 'shower', 'toilet', 'sink', 'tap',
        # Request phrases
        'need more', 'need extra', 'need new', 'replace', 'change',
        'please clean', 'please fix', 'help with', 'can you clean'
    ]
    
    if any(keyword in user_lower for keyword in housekeeping_keywords):
        return 'housekeeping'

    # FAQ: Hotel information requests
    faq_keywords = [
        'wifi', 'password', 'internet', 'location', 'address', 'where',
        'what time', 'when', 'how', 'parking', 'breakfast', 'amenities',
        'pool', 'gym', 'restaurant', 'check-in time', 'check-out time',
        'direction', 'directions', 'get to', 'find', 'map', 'nearby',
        'timing', 'hours', 'open', 'close', 'contact', 'phone',
        'what is', 'where is', 'how to', 'tell me about'
    ]
    
    if any(keyword in user_lower for keyword in faq_keywords):
        return 'faq'

    return 'other'

def llm_answer_faq(user_message, hotel_info):
    """
    Improved FAQ answering with better context understanding
    """
    prompt = f"""You are a helpful hotel assistant. Answer the guest's question using the hotel information provided.

Rules:
- Use ONLY the information from the hotel details below
- Be concise but complete
- If information is not available, politely say so and suggest contacting front desk
- Be friendly and professional
- Format your response clearly

Hotel Information:
{hotel_info}

Guest Question: {user_message}

Assistant Response:"""

    # Try LLM first
    llm_response = call_ollama(prompt, max_tokens=400)
    
    if llm_response and len(llm_response) > 20:
        return llm_response

    # Enhanced fallback keyword search
    user_lower = user_message.lower()
    relevant_sections = []
    
    # Split hotel info into sections and search
    sections = hotel_info.split('\n\n')
    
    for section in sections:
        if not section.strip():
            continue
            
        section_lower = section.lower()
        
        # Check if user question keywords appear in this section
        question_words = [word for word in user_lower.split() if len(word) > 3]
        matches = sum(1 for word in question_words if word in section_lower)
        
        if matches > 0:
            relevant_sections.append((section.strip(), matches))
    
    if relevant_sections:
        # Sort by relevance and return top sections
        relevant_sections.sort(key=lambda x: x[1], reverse=True)
        return '\n\n'.join([section[0] for section in relevant_sections[:2]])

    # Generic fallback
    return "I'm sorry, I don't have that specific information in my database. For detailed inquiries, please contact our front desk. I can also help you with check-in or housekeeping requests if needed."

def summarize_request(request_text):
    """
    Improved request summarization
    """
    prompt = f"""Summarize this hotel guest's housekeeping request in one clear, professional sentence.

Guest Request: "{request_text}"

Summary (one sentence):"""

    # Try LLM first
    llm_response = call_ollama(prompt, max_tokens=150)
    
    if llm_response and len(llm_response) > 10:
        return llm_response.strip()

    # Fallback: Clean up the original request
    cleaned = request_text.strip()
    if len(cleaned) > 100:
        cleaned = cleaned[:100] + "..."
    
    return cleaned
