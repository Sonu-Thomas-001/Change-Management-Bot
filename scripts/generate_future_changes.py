import requests
import os
import sys
import random
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

# Add the parent directory to sys.path to import app.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def generate_future_changes():
    """
    Generates 100 dummy Change Requests in ServiceNow for upcoming dates with diverse details.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        print("Error: ServiceNow credentials not found in environment variables.")
        return

    url = f"{INSTANCE}/api/now/table/change_request"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Data Pools for Random Generation
    actions = ["Upgrade", "Patch", "Install", "Decommission", "Reboot", "Configure", "Migrate", "Monitor", "Audit", "Backup", "Restore", "Optimize"]
    targets = ["Windows Server 2019", "Linux Cluster", "Oracle Database", "Core Switch", "Firewall", "Load Balancer", "CRM Application", "ERP System", "Email Gateway", "Storage SAN", "Virtual Host", "Kubernetes Node", "API Gateway", "DNS Server", "Active Directory"]
    environments = ["Production", "Staging", "Development", "DR Site", "Cloud Region A", "Cloud Region B"]
    
    categories = ["Hardware", "Software", "Network", "Database", "Security", "System", "Application", "Other"]
    risks = ["2", "3", "4"] # High, Moderate, Low (assuming 2,3,4 mapping, or 1,2,3)
    impacts = ["1", "2", "3"] # High, Medium, Low
    types = ["Normal", "Standard", "Emergency"]

    num_changes = 100
    print(f"Generating {num_changes} Diverse Change Requests...")

    success_count = 0
    fail_count = 0
    
    now = datetime.now()

    # --- Generate Future Changes (Disabled for now) ---
    # for i in range(num_changes):
    #     ... (future generation logic) ...

    # --- Generate Past Changes (Before Nov 2025) ---
    num_past_changes = 50
    print(f"\nGenerating {num_past_changes} Past Change Requests (Before Nov 2025)...")

    for i in range(num_past_changes):
        # 1. Generate Random Details
        action = random.choice(actions)
        target = random.choice(targets)
        env = random.choice(environments)
        
        short_desc = f"{action} {target} - {env}"
        description = f"Completed {action.lower()} on {target} in {env} environment."
        

        # 3. Determine Close Code (mostly successful)
        close_code = "successful" if random.random() > 0.1 else "unsuccessful"
        state = "3" # Closed

        payload = {
            "short_description": short_desc,
            "description": description,
            "category": category,
            "risk": risk,
            "impact": impact,
            "type": change_type,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "state": state, 
            "close_code": close_code,
            "close_notes": f"Change implemented {close_code}.",
            "assignment_group": "IT Operations"
        }

        print(f"[{i+1}/{num_past_changes}] Creating Past Change: {short_desc} ({start_date.strftime('%Y-%m-%d')})...")

        try:
            response = requests.post(
                url, 
                auth=HTTPBasicAuth(USER, PASSWORD), 
                json=payload, 
                headers=headers
            )

            if response.status_code == 201:
                data = response.json()
                number = data['result'].get('number')
                print(f"  -> Success! Ticket: {number}")
                success_count += 1
            else:
                print(f"  -> Failed. Status: {response.status_code}, Error: {response.text}")
                fail_count += 1
        except Exception as e:
            print(f"  -> Error: {e}")
            fail_count += 1

    print(f"\nGeneration Completed.")
    print(f"Total Success: {success_count}")
    print(f"Total Failed: {fail_count}")

if __name__ == "__main__":
    generate_future_changes()
