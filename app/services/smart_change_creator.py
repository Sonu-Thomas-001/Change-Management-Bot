import os
import requests
from flask import session, jsonify
from requests.auth import HTTPBasicAuth
import datetime

# --- Mock Data for Search ---
MOCK_SUCCESSFUL_CHANGES = [
    {
        "number": "CHG003001",
        "short_description": "Upgrade Oracle Database to 19c",
        "description": "Full upgrade of the primary Oracle DB instance. Includes backup verification and rollback plan.",
        "risk": "High",
        "impact": "2 - Medium",
        "type": "Normal",
        "implementation_plan": "1. Stop App Services\n2. Backup DB\n3. Run Upgrade Script\n4. Verify Version\n5. Start Services",
        "close_code": "Successful"
    },
    {
        "number": "CHG003002",
        "short_description": "Patch Windows Server 2019 Fleet",
        "description": "Apply monthly security patches to all Windows 2019 servers in the production environment.",
        "risk": "Low",
        "impact": "3 - Low",
        "type": "Standard",
        "implementation_plan": "1. Reboot servers one by one\n2. Verify uptime",
        "close_code": "Successful"
    },
    {
        "number": "CHG003003",
        "short_description": "Firewall Rule Update for Vendor Access",
        "description": "Allow specific IP range for new vendor API access on port 443.",
        "risk": "Low",
        "impact": "3 - Low",
        "type": "Standard",
        "implementation_plan": "1. Backup config\n2. Add rule\n3. Test connectivity",
        "close_code": "Successful"
    }
]

def search_similar_changes(query):
    """
    Mock search for successful past changes based on keywords.
    In a real scenario, this would query ServiceNow or a vector DB.
    """
    query_lower = query.lower()
    matches = []
    
    for change in MOCK_SUCCESSFUL_CHANGES:
        # Simple keyword matching
        if any(word in change['short_description'].lower() for word in query_lower.split()):
            matches.append(change)
            
    return matches

def clone_change_request(ticket_number):
    """
    Retrieves details of a specific ticket to use as a clone.
    """
    for change in MOCK_SUCCESSFUL_CHANGES:
        if change['number'] == ticket_number:
            return change.copy()
    return None

def create_change_request_mock(draft):
    """
    Mock creation of a change request in ServiceNow.
    """
    import random
    new_id = f"CHG{random.randint(4000, 9999)}"
    return new_id

def process_smart_change_intent(question):
    """
    Main handler for the Smart Change Creator feature.
    Manages conversation state via Flask session.
    """
    question_lower = question.lower()
    
    # --- STATE 2: Awaiting Clone Confirmation ---
    if session.get('smart_change_state') == 'awaiting_clone_confirmation':
        if any(word in question_lower for word in ['yes', 'sure', 'ok', 'yeah', 'confirm']):
            # User accepted the clone
            suggestion = session.get('smart_change_suggestion')
            if not suggestion:
                session.pop('smart_change_state', None)
                return jsonify({"answer": "Session expired. Please start over."})
            
            # Create draft in session
            draft = suggestion.copy()
            session['smart_change_draft'] = draft
            session['smart_change_state'] = 'awaiting_details'
            
            return jsonify({
                "answer": (
                    f"✅ **Cloning {draft['number']}...**\n\n"
                    f"I've pre-filled the description: *{draft['short_description']}*\n"
                    f"Risk: *{draft['risk']}* | Type: *{draft['type']}*\n\n"
                    "Please provide the **Planned Start Date** for this new request (e.g., YYYY-MM-DD)."
                )
            })
        elif any(word in question_lower for word in ['no', 'cancel', 'stop']):
            session.pop('smart_change_state', None)
            session.pop('smart_change_suggestion', None)
            return jsonify({"answer": "❌ Smart Change Creation cancelled."})
        else:
            # Ambiguous response, keep state
            return jsonify({"answer": "Please answer **Yes** to clone this ticket or **No** to cancel."})

    # --- STATE 3: Awaiting Details (Date) ---
    elif session.get('smart_change_state') == 'awaiting_details':
        # Simple date validation (can be improved)
        import re
        date_match = re.search(r'\d{4}-\d{1,2}-\d{1,2}', question)
        if date_match:
            draft = session.get('smart_change_draft')
            draft['start_date'] = date_match.group(0)
            
            # Proceed to creation
            new_id = create_change_request_mock(draft)
            
            # Clear session
            session.pop('smart_change_state', None)
            session.pop('smart_change_draft', None)
            session.pop('smart_change_suggestion', None)
            
            return jsonify({
                "answer": (
                    f"🎉 **Success!** New Change Request **{new_id}** has been created.\n\n"
                    f"**Details:**\n"
                    f"- **Description:** {draft['short_description']}\n"
                    f"- **Start Date:** {draft['start_date']}\n"
                    f"- **Cloned From:** {draft['number']}\n\n"
                    f"[View in ServiceNow](#)"
                )
            })
        else:
            return jsonify({"answer": "⚠️ I need a valid date (YYYY-MM-DD) to proceed with the creation."})

    # --- STATE 1: Initial Intent Detection ---
    # Only trigger if "create" and "change" are present, and NOT already in a flow
    if "create" in question_lower and "change" in question_lower:
        # Search for similar changes
        matches = search_similar_changes(question)
        
        if matches:
            best_match = matches[0]
            session['smart_change_state'] = 'awaiting_clone_confirmation'
            session['smart_change_suggestion'] = best_match
            
            details = (
                f"**{best_match['number']} - {best_match['short_description']}**\n"
                f"- **Risk:** {best_match['risk']}\n"
                f"- **Type:** {best_match['type']}\n"
                f"- **Plan:** {best_match['implementation_plan'][:100]}..."
            )
            
            return jsonify({
                "answer": (
                    f"💡 **Smart Suggestion:** I found a successful past change that matches your intent.\n\n"
                    f"{details}\n\n"
                    f"Would you like to use **{best_match['number']}** as a template? (Yes/No)"
                )
            })
    
    # If no state matched and no new intent found, return None to let app.py handle it
    return None
