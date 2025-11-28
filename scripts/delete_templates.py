import requests
import os
import sys
from requests.auth import HTTPBasicAuth

# Add the parent directory to sys.path to import app.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def delete_templates():
    """
    Deletes templates from ServiceNow where name starts with 'ABC'.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        print("Error: ServiceNow credentials not found in environment variables.")
        return

    url = f"{INSTANCE}/api/now/table/sys_template"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        # 1. Find templates to delete
        print("Searching for templates to delete (name starts with 'ABC')...")
        query = "nameSTARTSWITHABC"
        params = {
            "sysparm_query": query,
            "sysparm_fields": "sys_id,name",
            "sysparm_limit": 500 # Adjust limit if needed, though we imported 200
        }

        response = requests.get(
            url, 
            auth=HTTPBasicAuth(USER, PASSWORD), 
            params=params, 
            headers=headers
        )

        if response.status_code != 200:
            print(f"Error searching templates: {response.status_code} - {response.text}")
            return

        templates = response.json().get('result', [])
        count = len(templates)
        
        if count == 0:
            print("No templates found matching the criteria.")
            return

        print(f"Found {count} templates. Starting deletion...")

        # 2. Delete each template
        success_count = 0
        fail_count = 0

        for t in templates:
            sys_id = t['sys_id']
            name = t['name']
            
            delete_url = f"{url}/{sys_id}"
            del_response = requests.delete(
                delete_url,
                auth=HTTPBasicAuth(USER, PASSWORD),
                headers=headers
            )

            if del_response.status_code == 204:
                print(f"  [x] Deleted: {name}")
                success_count += 1
            else:
                print(f"  [!] Failed to delete {name}: {del_response.status_code}")
                fail_count += 1

        print(f"\nDeletion Completed.")
        print(f"Total Deleted: {success_count}")
        print(f"Total Failed: {fail_count}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    delete_templates()
