import requests
from requests.auth import HTTPBasicAuth
from app.config import Config
from app.services.smart_change_creator import find_relevant_templates
import random
from datetime import datetime, timedelta

def create_dummy_change(template, keyword):
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    if not all([INSTANCE, USER, PASSWORD]):
        print("Skipping: ServiceNow credentials not configured.")
        return

    url = f"{INSTANCE}/api/now/table/change_request"
    
    # Randomize date in the past 30 days
    days_ago = random.randint(1, 30)
    closed_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    
    payload = {
        "short_description": f"Executed: {template.get('short_description', 'Change')} - {keyword.capitalize()}",
        "description": f"This change was executed based on the template: {template.get('name')}. \n\n{template.get('description', '')}",
        "risk": template.get('risk', '3'),
        "impact": template.get('impact', '3'),
        "type": template.get('type', 'Normal'),
        "state": "-5", # New
        "assignment_group": "Network", # Defaulting to Network for now
        "assigned_to": USER
    }
    
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, auth=HTTPBasicAuth(USER, PASSWORD), json=payload, headers=headers)
        if response.status_code == 201:
            data = response.json()
            number = data['result'].get('number')
            print(f"✅ Created Closed Change: {number} for template '{template.get('name')}'")
        else:
            print(f"❌ Failed to create change: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("Starting population of dummy changes...")
    
    keywords = ["Firewall", "Patch", "Server", "Database", "Network", "Upgrade", "Maintenance"]
    
    for keyword in keywords:
        print(f"\nSearching templates for keyword: {keyword}")
        templates = find_relevant_templates(keyword)
        
        if not templates:
            print(f"No templates found for {keyword}")
            continue
            
        for template in templates:
            # Create 2 dummy changes for each template
            for _ in range(2):
                create_dummy_change(template, keyword)
                
    print("\nPopulation complete!")

if __name__ == "__main__":
    main()
