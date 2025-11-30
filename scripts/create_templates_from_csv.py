import csv
import requests
import os
import sys
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables directly
load_dotenv()

def create_templates_from_csv(csv_file_path):
    """
    Reads a CSV file and creates or updates standard change templates in ServiceNow.
    Renames existing templates to include the template number.
    """
    INSTANCE = os.environ.get("SERVICENOW_INSTANCE")
    USER = os.environ.get("SERVICENOW_USER")
    PASSWORD = os.environ.get("SERVICENOW_PASSWORD")

    if not all([INSTANCE, USER, PASSWORD]):
        print("Error: ServiceNow credentials not found in environment variables.")
        return

    url = f"{INSTANCE}/api/now/table/sys_template"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            success_count = 0
            # Store rows to update CSV later
            all_rows = []
            fieldnames = reader.fieldnames
            if 'sys_id' not in fieldnames:
                fieldnames.append('sys_id')

            for row in reader:
                template_name = row.get('Name')
                template_number = row.get('template_number')
                
                if not template_name:
                    print("Skipping row with missing Name")
                    all_rows.append(row)
                    continue

                target_name = f"{template_number} - {template_name}" if template_number else template_name
                
                # Check if template exists
                query_new = f"table=change_request^name={target_name}"
                params_new = {"sysparm_query": query_new, "sysparm_fields": "sys_id,name"}
                resp_new = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params_new, headers=headers)
                
                existing_sys_id = None
                if resp_new.status_code == 200:
                    results = resp_new.json().get('result', [])
                    if results:
                        existing_sys_id = results[0]['sys_id']
                        print(f"Found existing template '{target_name}' (ID: {existing_sys_id}). Updating...")

                # Construct the 'template' field (Values to be pre-filled in the Change Request)
                template_values = []
                template_values.append("type=standard") # Default to standard
                
                if row.get('Application'):
                    template_values.append(f"category={row['Application']}")
                
                if row.get('CR_Short_description'):
                    template_values.append(f"short_description={row['CR_Short_description']}")
                
                if row.get('CR_Description'):
                    template_values.append(f"description={row['CR_Description']}")
                
                if row.get('Implementation_plan'):
                    template_values.append(f"implementation_plan={row['Implementation_plan']}")

                if row.get('Backout_plan'):
                    template_values.append(f"backout_plan={row['Backout_plan']}")

                if row.get('Test_plan'):
                    template_values.append(f"test_plan={row['Test_plan']}")

                template_string = "^".join(template_values) + "^EQ"

                payload = {
                    "name": target_name,
                    "short_description": row.get('Short_description'),
                    "table": "change_request",
                    "template": template_string,
                    "active": row.get('Active', 'true').lower(),
                    "group": "Change Management" # Default group
                }

                current_sys_id = existing_sys_id

                if existing_sys_id:
                    # UPDATE existing - SKIPPING to speed up sys_id population
                    # update_url = f"{url}/{existing_sys_id}"
                    # response = requests.put(
                    #     update_url, 
                    #     auth=HTTPBasicAuth(USER, PASSWORD), 
                    #     json=payload, 
                    #     headers=headers
                    # )
                    # if response.status_code == 200:
                    #     print(f"  -> Update Success!")
                    #     updated_count += 1
                    # else:
                    #     print(f"  -> Update Failed. Status: {response.status_code}, Error: {response.text}")
                    #     fail_count += 1
                    print(f"  -> Exists (Skipping Update). Sys ID: {current_sys_id}")
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
                        current_sys_id = data['result'].get('sys_id')
                        print(f"  -> Create Success! Sys ID: {current_sys_id}")
                        success_count += 1
                    else:
                        print(f"  -> Create Failed. Status: {response.status_code}, Error: {response.text}")
                        fail_count += 1
                
                # Update row with sys_id
                if current_sys_id:
                    row['sys_id'] = current_sys_id
                all_rows.append(row)

            print(f"\nImport/Update Completed.")
            print(f"Total Created: {success_count}")
            print(f"Total Updated: {updated_count}")
            print(f"Total Failed: {fail_count}")
            
            # Write back to CSV with sys_id
            print("Updating CSV with sys_ids...")
            with open(csv_file_path, mode='w', encoding='utf-8-sig', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print("CSV updated successfully.")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Point to the correct CSV file
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "change_templates.csv")
    create_templates_from_csv(csv_path)
