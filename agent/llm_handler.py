import requests
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# For LLM integration (Ollama Mistral 7B)
def llm_classify_intent(user_message):
    """
    Classify user intent using Ollama Mistral 7B (local API call).
    Returns: 'check_in', 'faq', 'housekeeping', 'other'
    """
    # Example: Replace with actual Ollama API call
    if any(k in user_message for k in ['check in', 'booking', 'reservation']):
        return 'check_in'
    if any(k in user_message for k in ['clean', 'housekeeping', 'room service']):
        return 'housekeeping'
    if any(k in user_message for k in ['wifi', 'amenities', 'location', 'check-in', 'check-out', 'address', 'contact']):
        return 'faq'
    return 'other'

def llm_answer_faq(user_message, hotel_info):
    """
    Use Ollama Mistral 7B to answer FAQ using hotel_info.txt context.
    """
    # Example: Replace with actual Ollama API call
    # For now, simple keyword search
    for line in hotel_info.splitlines():
        if user_message.lower() in line.lower():
            return line
    return "I'm sorry, I don't have that information. Please ask the front desk."

def summarize_request(request_text):
    """
    Use LLM to summarize housekeeping request.
    """
    # Example: Replace with actual Ollama API call
    return f"Housekeeping request summary: {request_text[:100]}..."

def send_housekeeping_email(request_summary):
    """
    Send housekeeping request summary to jeevansuresh258@gmail.com
    """
    EMAIL_ADDRESS = os.environ.get('HOTEL_AGENT_EMAIL', 'your@email.com')
    EMAIL_PASSWORD = os.environ.get('HOTEL_AGENT_PASS', 'yourpassword')
    msg = EmailMessage()
    msg['Subject'] = 'New Housekeeping Request'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'jeevansuresh258@gmail.com'
    msg.set_content(request_summary)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
