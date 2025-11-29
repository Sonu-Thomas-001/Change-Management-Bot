import requests
from requests.auth import HTTPBasicAuth
from app.config import Config
from datetime import datetime

def find_similar_changes(description):
    """
    Searches for successful closed changes that match the description.
    Returns the best match as a dictionary or None.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    # --- MOCK MODE ---
    if not all([INSTANCE, USER, PASSWORD]):
        # Mock logic for testing without credentials
        if "database" in description.lower():
            return {
                "number": "CR-1024",
                "short_description": "Database Migration to AWS",
                "description": "Full migration of the legacy Oracle database to AWS RDS.",
                "risk": "High",
                "impact": "2 - Medium",
                "type": "Normal",
                "close_code": "Successful"
            }
        elif "switch" in description.lower():
             return {
                "number": "CHG0030001",
                "short_description": "Core Switch Upgrade",
                "description": "Upgrading firmware on the core switch stack.",
                "risk": "Very High",
                "impact": "1 - High",
                "type": "Normal",
                "close_code": "Successful"
            }
        return None

    # --- REAL SERVICENOW MODE ---
    try:
        url = f"{INSTANCE}/api/now/table/change_request"
        
        # Improve keyword extraction
        import re
        # Remove special chars and lowercase
        clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', description.lower())
        words = clean_desc.split()
        
        stop_words = {'i', 'need', 'to', 'a', 'an', 'the', 'for', 'of', 'in', 'on', 'at', 'with', 'create', 'change', 'request', 'ticket', 'please', 'update', 'upgrade', 'fix', 'issue'}
        keywords = [w for w in words if w not in stop_words]
        
        # If no keywords left (e.g. "create a change"), fallback to original or empty
        if not keywords:
            keywords = words[:3]
            
        # Take top 3 meaningful keywords
        search_terms = keywords[:3]
        
        if not search_terms:
            return None
            
        keyword_query = "^".join([f"short_descriptionLIKE{k}" for k in search_terms])
        
        query = f"active=false^close_code=successful^{keyword_query}"
        
        params = {
            "sysparm_query": query,
            "sysparm_limit": 1,
            "sysparm_fields": "number,short_description,description,risk,impact,type,close_code",
            "sysparm_display_value": "true"
        }
        
        headers = {"Accept": "application/json"}
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and len(data['result']) > 0:
                return data['result'][0]
                
        return None

    except Exception as e:
        print(f"Smart Change Search Error: {e}")
        return None

def get_change_details(ticket_number):
    """
    Fetches details of a specific change request.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    # --- MOCK MODE ---
    if not all([INSTANCE, USER, PASSWORD]):
        return {
            "number": ticket_number,
            "short_description": "Mock Change Request",
            "description": "This is a mock description for testing.",
            "risk": "Low",
            "impact": "3 - Low",
            "type": "Normal"
        }

    # --- REAL SERVICENOW MODE ---
    try:
        url = f"{INSTANCE}/api/now/table/change_request"
        params = {
            "sysparm_query": f"number={ticket_number}",
            "sysparm_limit": 1,
            "sysparm_fields": "number,short_description,description,risk,impact,type",
            "sysparm_display_value": "true"
        }
        
        headers = {"Accept": "application/json"}
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and len(data['result']) > 0:
                return data['result'][0]
        
        return None
    except Exception as e:
        print(f"Get Change Details Error: {e}")
        return None

def create_change_request(template_ticket, start_date, end_date, assigned_to="Unassigned"):
    """
    Creates a new change request based on a template ticket.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    # --- MOCK MODE ---
    if not all([INSTANCE, USER, PASSWORD]):
        return "CHG_NEW_9999"

    # --- REAL SERVICENOW MODE ---
    try:
        url = f"{INSTANCE}/api/now/table/change_request"
        
        payload = {
            "short_description": f"CLONE: {template_ticket.get('short_description')}",
            "description": template_ticket.get('description', ''),
            "risk": template_ticket.get('risk'),
            "impact": template_ticket.get('impact'),
            "type": template_ticket.get('type'),
            "start_date": start_date,
            "end_date": end_date,
            "assigned_to": assigned_to
            # Add other fields as needed
        }
        
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(url, auth=HTTPBasicAuth(USER, PASSWORD), json=payload, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            if 'result' in data:
                return data['result'].get('number')
        
        print(f"Creation Failed: {response.text}")
        return None

    except Exception as e:
        print(f"Smart Change Creation Error: {e}")
        return None

def find_relevant_templates(query):
    """
    Searches for relevant templates in the sys_template table based on the query.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    # --- MOCK MODE ---
    if not all([INSTANCE, USER, PASSWORD]):
        # Mock logic
        if "oracle" in query.lower():
            return [
                {"name": "Oracle Major Upgrade", "short_description": "Upgrade Oracle DB to 19c", "template": "risk=High^impact=2"},
                {"name": "Oracle Patching", "short_description": "Apply quarterly patches", "template": "risk=Low^impact=3"}
            ]
        return []

    # --- REAL SERVICENOW MODE ---
    try:
        url = f"{INSTANCE}/api/now/table/sys_template"
        
        # Simple keyword extraction
        import re
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query.lower())
        words = clean_q.split()
        stop_words = {'i', 'need', 'to', 'a', 'an', 'the', 'for', 'of', 'in', 'on', 'at', 'with', 'create', 'change', 'request', 'ticket', 'please', 'update', 'upgrade', 'fix', 'issue', 'template', 'which', 'use', 'should'}
        keywords = [w for w in words if w not in stop_words]
        
        if not keywords:
            keywords = words[:1] # Fallback
            
        # Sort keywords by length (descending) to prioritize specific terms like "firewall" over "new"
        keywords.sort(key=len, reverse=True)
        
        # Take top 2 keywords
        search_terms = keywords[:2]
        
        if not search_terms:
             return []

        # Build query: Search for the most specific term (longest)
        # If we have multiple terms, we could try to AND them or just search the primary one.
        # Let's search for the primary term (longest)
        term = search_terms[0]
        sn_query = f"table=change_request^active=true^nameLIKE{term}^ORshort_descriptionLIKE{term}"
        
        params = {
            "sysparm_query": sn_query,
            "sysparm_limit": 5,
            "sysparm_fields": "sys_id,name,short_description,template",
            "sysparm_display_value": "true"
        }
        
        headers = {"Accept": "application/json"}
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        
        if response.status_code == 200:
            results = response.json().get('result', [])
            if results:
                return results
        
        # Fallback: If no templates found (or search failed), try to find the generic template
        print("No specific templates found. Searching for generic template ABC00000...")
        fallback_query = "table=change_request^active=true^nameSTARTSWITHABC00000"
        
        params = {
            "sysparm_query": fallback_query,
            "sysparm_limit": 1,
            "sysparm_fields": "sys_id,name,short_description,template",
            "sysparm_display_value": "true"
        }
        
        fallback_response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        if fallback_response.status_code == 200:
            return fallback_response.json().get('result', [])
            
        return []

    except Exception as e:
        print(f"Template Search Error: {e}")
        return []
