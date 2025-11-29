import csv
import requests
import os
import sys
from requests.auth import HTTPBasicAuth

# Add the parent directory to sys.path to import app.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def create_templates_from_csv(csv_file_path):
    """
    Reads a CSV file and creates or updates standard change templates in ServiceNow.
    Renames existing templates to include the template number.
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
            updated_count = 0
            fail_count = 0

            for row in reader:
                template_name = row.get('template_name')
                template_number = row.get('template_number')
                
                if not template_name:
                    print("Skipping row with missing template_name")
                    continue

                target_name = f"{template_number} - {template_name}" if template_number else template_name
                
                # Check if template exists with OLD name
                query_old = f"table=change_request^name={template_name}"
                params_old = {"sysparm_query": query_old, "sysparm_fields": "sys_id,name"}
                resp_old = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params_old, headers=headers)
                
                existing_sys_id = None
                if resp_old.status_code == 200:
                    results = resp_old.json().get('result', [])
                    if results:
                        existing_sys_id = results[0]['sys_id']
                        print(f"Found existing template '{template_name}' (ID: {existing_sys_id}). Renaming to '{target_name}'...")

                # If not found by old name, check by NEW name (to avoid duplicates if re-run)
                if not existing_sys_id:
                    query_new = f"table=change_request^name={target_name}"
                    params_new = {"sysparm_query": query_new, "sysparm_fields": "sys_id,name"}
                    resp_new = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params_new, headers=headers)
                    if resp_new.status_code == 200:
                        results = resp_new.json().get('result', [])
                        if results:
                            print(f"Template '{target_name}' already exists. Skipping creation.")
                            success_count += 1 # Count as success since it exists
                            continue

                # Map 'Approval Model' to 'type'
                approval_model = row.get('Approval Model', '').lower()
                change_type = "normal" # Default
                if "standard" in approval_model or "auto" in approval_model:
                    change_type = "standard"
                elif "emergency" in approval_model:
                    change_type = "emergency"
                
                # Construct the 'template' field
                template_values = []
                template_values.append(f"type={change_type}")
                
                if row.get('Change Type'):
                    template_values.append(f"category={row['Change Type']}")
                
                description_parts = []
                if row.get('Usage'):
                    description_parts.append(row['Usage'])
                if row.get('Applicable Scenarios'):
                    description_parts.append(f"Applicable Scenarios:\n{row['Applicable Scenarios']}")
                
                full_description = "\n\n".join(description_parts)
                if full_description:
                     template_values.append(f"description={full_description}")

                if row.get('Owning Group'):
                    template_values.append(f"assignment_group={row['Owning Group']}")
                
                if row.get('Lead Time'):
                     template_values.append(f"implementation_plan=Lead Time: {row['Lead Time']}")

                template_string = "^".join(template_values) + "^EQ"

                payload = {
                    "name": target_name,
                    "short_description": row.get('Short description'),
                    "table": "change_request",
                    "template": template_string,
                    "active": row.get('Active', 'true').lower(),
                    "group": row.get('Group', '') 
                }

                if existing_sys_id:
                    # UPDATE existing
                    update_url = f"{url}/{existing_sys_id}"
                    response = requests.put(
                        update_url, 
                        auth=HTTPBasicAuth(USER, PASSWORD), 
                        json=payload, 
                        headers=headers
                    )
                    if response.status_code == 200:
                        print(f"  -> Update Success!")
                        updated_count += 1
                    else:
                        print(f"  -> Update Failed. Status: {response.status_code}, Error: {response.text}")
                        fail_count += 1
                else:
                    # CREATE new
                    print(f"Creating new template: {target_name}...")
                    response = requests.post(
                        url, 
                        auth=HTTPBasicAuth(USER, PASSWORD), 
                        json=payload, 
                        headers=headers
                    )

                    if response.status_code == 201:
                        data = response.json()
                        sys_id = data['result'].get('sys_id')
                        print(f"  -> Create Success! Sys ID: {sys_id}")
                        success_count += 1
                    else:
                        print(f"  -> Create Failed. Status: {response.status_code}, Error: {response.text}")
                        fail_count += 1

            print(f"\nImport/Update Completed.")
            print(f"Total Created/Existing: {success_count}")
            print(f"Total Updated: {updated_count}")
            print(f"Total Failed: {fail_count}")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), "standard_change_templates_200.csv")
    create_templates_from_csv(csv_path)
