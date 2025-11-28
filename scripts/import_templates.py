import csv
import requests
import os
import sys
from requests.auth import HTTPBasicAuth

# Add the parent directory to sys.path to import app.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def import_templates(csv_file_path):
    """
    Reads a CSV file and creates templates in ServiceNow.
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
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            success_count = 0
            fail_count = 0

            for row in reader:
                # Map CSV columns to ServiceNow sys_template fields
                # CSV Columns: template_number, template_name, template_description, proposal_type, category, description
                
                # Construct the 'template' field which holds the encoded field values for the target record
                # Format: field1=value1^field2=value2^EQ
                template_values = []
                if row.get('proposal_type'):
                    template_values.append(f"type={row['proposal_type']}")
                if row.get('category'):
                    template_values.append(f"category={row['category']}")
                if row.get('description'):
                    template_values.append(f"description={row['description']}")
                
                # Add EQ at the end
                template_string = "^".join(template_values) + "^EQ"

                payload = {
                    "name": row.get('template_name'),
                    "short_description": row.get('template_description'),
                    "table": "change_request",
                    "template": template_string,
                    "active": "true",
                    "user": "", # Global template if empty? Or assign to specific user? Leaving empty for global/group visibility usually requires roles.
                    "group": "" 
                }

                print(f"Creating template: {row.get('template_name')}...")

                response = requests.post(
                    url, 
                    auth=HTTPBasicAuth(USER, PASSWORD), 
                    json=payload, 
                    headers=headers
                )

                if response.status_code == 201:
                    data = response.json()
                    sys_id = data['result'].get('sys_id')
                    print(f"  -> Success! Sys ID: {sys_id}")
                    success_count += 1
                else:
                    print(f"  -> Failed. Status: {response.status_code}, Error: {response.text}")
                    fail_count += 1

            print(f"\nImport Completed.")
            print(f"Total Success: {success_count}")
            print(f"Total Failed: {fail_count}")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), "standard_change_templates_200.csv")
    import_templates(csv_path)
