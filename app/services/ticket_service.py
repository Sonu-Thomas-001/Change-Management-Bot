import requests
from flask import jsonify
from requests.auth import HTTPBasicAuth
from app.config import Config

def get_ticket_details(ticket_number):
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    # Mock Mode
    if ticket_number.startswith("MOCK-") or not all([INSTANCE, USER, PASSWORD]):
        mock_db = {
            "CR-1024": {
                "state": "Implement", 
                "priority": "2 - High", 
                "short_description": "Database Migration",
                "risk": "High",
                "impact": "2 - Medium",
                "assigned_to": "David L.",
                "assignment_group": "Database Team",
                "start_date": "2023-12-01 08:00:00",
                "end_date": "2023-12-01 12:00:00",
                "type": "Normal"
            },
            "MOCK-1024": {
                "state": "Implement", 
                "priority": "2 - High", 
                "short_description": "Database Migration",
                "risk": "High",
                "impact": "2 - Medium",
                "assigned_to": "David L.",
                "assignment_group": "Database Team",
                "start_date": "2023-12-01 08:00:00",
                "end_date": "2023-12-01 12:00:00",
                "type": "Normal"
            },
            "CR-1001": {
                "state": "New", 
                "priority": "4 - Low", 
                "short_description": "Firewall Rule Update",
                "risk": "Low",
                "impact": "3 - Low",
                "assigned_to": "Sarah C.",
                "assignment_group": "Network Security",
                "start_date": "2023-12-05 10:00:00",
                "end_date": "2023-12-05 11:00:00",
                "type": "Standard"
            }
        }
        ticket = mock_db.get(ticket_number)
        if ticket:
            details = (
                f"**{ticket_number}** Details:\n\n"
                f"*   **Description:** {ticket['short_description']}\n"
                f"*   **Type:** {ticket.get('type', 'N/A')}\n"
                f"*   **State:** {ticket['state']}\n"
                f"*   **Priority:** {ticket['priority']}\n"
                f"*   **Risk:** {ticket['risk']}\n"
                f"*   **Impact:** {ticket['impact']}\n"
                f"*   **Assigned To:** {ticket['assigned_to']} ({ticket['assignment_group']})\n"
                f"*   **Planned Start:** {ticket['start_date']}\n"
                f"*   **Planned End:** {ticket['end_date']}"
            )
            return jsonify({"answer": details})
        else:
            return jsonify({"answer": f"I couldn't find any record for **{ticket_number}**."})

    url = f"{INSTANCE}/api/now/table/change_request"
    params = {
        "sysparm_query": f"number={ticket_number}",
        "sysparm_limit": 1,
        "sysparm_fields": "state,priority,short_description,risk,impact,assigned_to,assignment_group,start_date,end_date,type",
        "sysparm_display_value": "true"
    }
    
    try:
        headers = {"Accept": "application/json"}
        # Disable redirects to catch 302s (often login pages)
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers, allow_redirects=False)
        
        if response.status_code in [301, 302]:
             return jsonify({"answer": f"⚠️ ServiceNow API Redirected (Status {response.status_code}).\n\n**Target:** `{response.headers.get('Location')}`\n**Requested URL:** `{url}`\n\n**Possible Fix:** Check your `SERVICENOW_INSTANCE` in `.env`. It should look like `https://dev12345.service-now.com` (no trailing slash)."})

        if response.status_code != 200:
            return jsonify({"answer": f"ServiceNow API Error: Status {response.status_code} - {response.text[:200]}"})
            
        if not response.text.strip():
             return jsonify({"answer": f"ServiceNow API returned an empty response (Status 200). Content-Type: {response.headers.get('Content-Type')}"})

        try:
            data = response.json()
        except ValueError:
             # If we still get invalid JSON with 200 OK and text/html, it's likely a misconfigured instance returning a default page
             return jsonify({"answer": f"ServiceNow API returned invalid JSON.\n**Status:** {response.status_code}\n**Content-Type:** {response.headers.get('Content-Type')}\n**URL:** `{url}`\n**Response:** `{response.text[:500]}`"})
        if 'result' in data and len(data['result']) > 0:
            ticket = data['result'][0]
            
            def get_val(key):
                val = ticket.get(key)
                if isinstance(val, dict) and 'display_value' in val:
                    return val['display_value']
                return val if val else "N/A"

            details = (
                f"**{ticket_number}** Details:\n\n"
                f"*   **Description:** {get_val('short_description')}\n"
                f"*   **Type:** {get_val('type')}\n"
                f"*   **State:** {get_val('state')}\n"
                f"*   **Priority:** {get_val('priority')}\n"
                f"*   **Risk:** {get_val('risk')}\n"
                f"*   **Impact:** {get_val('impact')}\n"
                f"*   **Assigned To:** {get_val('assigned_to')}\n"
                f"*   **Assignment Group:** {get_val('assignment_group')}\n"
                f"*   **Planned Start:** {get_val('start_date')}\n"
                f"*   **Planned End:** {get_val('end_date')}"
            )
            return jsonify({"answer": details})
        else:
            return jsonify({"answer": f"Ticket **{ticket_number}** not found in ServiceNow."})
    except Exception as e:
        return jsonify({"answer": f"Error connecting to ServiceNow: {str(e)}"})
