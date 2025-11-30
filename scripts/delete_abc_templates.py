import requests
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SERVICENOW_INSTANCE = os.environ.get("SERVICENOW_INSTANCE")
    SERVICENOW_USER = os.environ.get("SERVICENOW_USER")
    SERVICENOW_PASSWORD = os.environ.get("SERVICENOW_PASSWORD")

def delete_abc_templates():
    """
    Deletes all standard change templates where name starts with 'ABC'.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        print("Error: ServiceNow credentials not found in environment variables.")
        return

    url = f"{INSTANCE}/api/now/table/sys_template"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Query for templates starting with ABC
    query = "table=change_request^nameSTARTSWITHABC"
    params = {
        "sysparm_query": query,
        "sysparm_fields": "sys_id,name"
    }

    print(f"Searching for templates matching: {query} ...")
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching templates: {response.status_code} - {response.text}")
            return

        results = response.json().get('result', [])
        count = len(results)
        print(f"Found {count} templates to delete.")

        if count == 0:
            return

        deleted_count = 0
        failed_count = 0

        for item in results:
            sys_id = item['sys_id']
            name = item['name']
            
            print(f"Deleting '{name}' ({sys_id})...")
            
            delete_url = f"{url}/{sys_id}"
            del_resp = requests.delete(delete_url, auth=HTTPBasicAuth(USER, PASSWORD), headers=headers)
            
            if del_resp.status_code == 204:
                print(f"  -> Deleted.")
                deleted_count += 1
            else:
                print(f"  -> Failed to delete. Status: {del_resp.status_code}")
                failed_count += 1

        print(f"\nDeletion Completed.")
        print(f"Total Deleted: {deleted_count}")
        print(f"Total Failed: {failed_count}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    delete_abc_templates()
