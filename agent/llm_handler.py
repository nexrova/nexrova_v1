import requests
import os
from datetime import datetime

# Ollama API Configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral')

def call_ollama(prompt, model=OLLAMA_MODEL, max_tokens=500):
    """
    Call Ollama API for LLM inference.

    Args:
        prompt: The prompt to send to the LLM
        model: The model name (default: mistral)
        max_tokens: Maximum tokens in response

    Returns:
        str: The LLM response, or fallback response if Ollama is unavailable
    """
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            },
            timeout=10
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
    Classify user intent using Ollama Mistral 7B with fallback to keyword matching.
    Returns: 'check_in', 'faq', 'housekeeping', 'other'

    FIXED: Less aggressive classification, especially for check_in
    """
    prompt = f"""You are a hotel assistant. Classify the user's intent into ONE of these categories:
- check_in: User wants to START checking into their room (phrases like "I want to check in", "check me in")
- housekeeping: User needs cleaning, room service, towels, amenities, maintenance, or reports spills/issues
- faq: User is asking questions about hotel info, amenities, location, wifi, parking, directions
- other: Anything else, including statements about being already checked in

User message: "{user_message}"

Respond with ONLY ONE WORD: check_in, housekeeping, faq, or other.
Intent:"""

    # Try Ollama first
    llm_response = call_ollama(prompt, max_tokens=10)

    if llm_response:
        # Parse LLM response
        intent = llm_response.lower().strip()
        if 'check' in intent and 'in' in intent:
            return 'check_in'
        elif 'housekeeping' in intent or 'cleaning' in intent:
            return 'housekeeping'
        elif 'faq' in intent or 'question' in intent:
            return 'faq'
        elif any(word in intent for word in ['check_in', 'housekeeping', 'faq']):
            # Extract the exact word
            for word in ['check_in', 'housekeeping', 'faq', 'other']:
                if word in intent:
                    return word

    # Fallback to keyword matching
    user_lower = user_message.lower()

    # FIXED: More specific check-in keywords (avoid false positives)
    # Only trigger check_in if user is STARTING the process
    if any(phrase in user_lower for phrase in [
        'i want to check in',
        'i need to check in', 
        'check me in',
        'start check in',
        'begin check in',
        'checking in now'
    ]):
        return 'check_in'

    # Single word "check in" without context
    if user_lower.strip() in ['check in', 'check-in', 'checkin']:
        return 'check_in'

    # FIXED: Expanded housekeeping keywords - catches spills, damage, issues
    housekeeping_keywords = [
        # Cleaning
        'clean', 'housekeeping', 'room service', 'maid',
        # Items needed
        'towel', 'toilet paper', 'tissue', 'soap', 'shampoo', 'amenities',
        # Issues/problems
        'spill', 'spilled', 'dirty', 'mess', 'stain', 'wet',
        # Damage/maintenance
        'broken', 'fix', 'repair', 'maintenance', 'not working',
        # Requests
        'need more', 'need extra', 'need new', 'replace',
        # Food/drink spills
        'gravy', 'coffee', 'water', 'juice', 'food', 'drink',
        # Room issues
        'ac', 'air conditioning', 'heater', 'light', 'bulb', 'door', 'lock',
        # Bathroom
        'shower', 'bathtub', 'sink', 'tap', 'flush', 'toilet',
        # Requests
        'please clean', 'please fix', 'help with'
    ]

    if any(k in user_lower for k in housekeeping_keywords):
        return 'housekeeping'

    # FAQ keywords - FIXED: Added "direction" related terms
    if any(k in user_lower for k in ['wifi', 'password', 'amenities', 'location', 'address', 
                                       'check-in time', 'check-out time', 'contact', 'phone',
                                       'where', 'what', 'when', 'how', 'parking', 'breakfast',
                                       'direction', 'directions', 'get to', 'find', 'map',
                                       'timing', 'hours', 'open', 'close']):
        return 'faq'

    # FIXED: Statements about being already checked in -> 'other'
    if any(phrase in user_lower for phrase in ['already checked', 'already check', "i'm checked"]):
        return 'other'

    return 'other'

def llm_answer_faq(user_message, hotel_info):
    """
    Use Ollama Mistral 7B to answer FAQ using hotel_info.txt context, with fallback to keyword search.
    """
    prompt = f"""You are a helpful hotel assistant. Answer the guest's question using ONLY the information provided below. 
If the information is not available, politely say you don't have that information and suggest contacting the front desk.

Hotel Information:
{hotel_info}

Guest Question: {user_message}

Answer (be concise and helpful):"""

    # Try Ollama first
    llm_response = call_ollama(prompt, max_tokens=300)

    if llm_response and len(llm_response) > 20:
        return llm_response

    # Fallback to keyword search
    user_lower = user_message.lower()
    relevant_lines = []

    for line in hotel_info.splitlines():
        line = line.strip()
        if not line:
            continue

        # Check if any word from the question appears in this line
        words = user_lower.split()
        for word in words:
            if len(word) > 3 and word in line.lower():
                relevant_lines.append(line)
                break

    if relevant_lines:
        return "\n".join(relevant_lines[:3])  # Return top 3 relevant lines

    # Generic fallback
    return "I'm sorry, I don't have that specific information. Please contact the front desk at the number provided, or I can help you with check-in or housekeeping requests."

def summarize_request(request_text):
    """
    Use LLM to create a concise summary of housekeeping request.
    """
    prompt = f"""Summarize this hotel guest's housekeeping request in ONE clear sentence:

Guest request: "{request_text}"

Summary:"""

    # Try Ollama first
    llm_response = call_ollama(prompt, max_tokens=100)

    if llm_response and len(llm_response) > 10:
        return llm_response

    # Fallback: Return the original request (cleaned up)
    return request_text.strip()
