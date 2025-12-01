import os
import csv
import re
import requests
from datetime import datetime, timedelta
from flask import jsonify
from requests.auth import HTTPBasicAuth
from app.config import Config

def check_schedule_conflict(user_input):
    """Check if proposed date conflicts with freeze periods in ServiceNow or CSV."""
    
    # Extract date from user input
    proposed_date = None
    date_str = None
    
    # Pattern 1: YYYY-MM-DD
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', user_input)
    if match:
        try:
            proposed_date = datetime.strptime(match.group(0), "%Y-%m-%d")
            date_str = match.group(0)
        except: pass
    
    # Pattern 2: Month DD, YYYY
    if not proposed_date:
        match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', user_input, re.IGNORECASE)
        if match:
            try:
                date_str = f"{match.group(1)} {match.group(2)}, {match.group(3)}"
                proposed_date = datetime.strptime(date_str, "%B %d, %Y")
            except: pass
    
    # Pattern 3: DD Month YYYY
    if not proposed_date:
        match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', user_input, re.IGNORECASE)
        if match:
            try:
                date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                proposed_date = datetime.strptime(date_str, "%d %B %Y")
            except: pass

    # Pattern 4: Month DD (No Year) - Assume current or next year
    if not proposed_date:
        match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?', user_input, re.IGNORECASE)
        if match:
            try:
                current_year = datetime.now().year
                date_str = f"{match.group(1)} {match.group(2)}, {current_year}"
                temp_date = datetime.strptime(date_str, "%B %d, %Y")
                
                # If date is in the past (more than 30 days ago), assume next year
                if temp_date < datetime.now() - timedelta(days=30):
                    date_str = f"{match.group(1)} {match.group(2)}, {current_year + 1}"
                    proposed_date = datetime.strptime(date_str, "%B %d, %Y")
                else:
                    proposed_date = temp_date
            except: pass
    
    if not proposed_date:
        return jsonify({"answer": "I couldn't identify a specific date in your request. Please specify a date like 'December 15, 2023' or '2023-12-15'."})
    
    # Check for conflicts
    conflicts = []
    
    # Try ServiceNow API first
    if all([Config.SERVICENOW_INSTANCE, Config.SERVICENOW_USER, Config.SERVICENOW_PASSWORD]):
        try:
            url = f"{Config.SERVICENOW_INSTANCE}/api/now/table/change_request"
            start_check = (proposed_date - timedelta(days=1)).strftime("%Y-%m-%d")
            end_check = (proposed_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            params = {
                "sysparm_query": f"start_date>={start_check}^start_date<={end_check}^ORend_date>={start_check}^end_date<={end_check}",
                "sysparm_fields": "number,short_description,start_date,end_date,state,risk",
                "sysparm_display_value": "true",
                "sysparm_limit": 10
            }
            
            response = requests.get(url, auth=HTTPBasicAuth(Config.SERVICENOW_USER, Config.SERVICENOW_PASSWORD), params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and len(data['result']) > 0:
                    for change in data['result']:
                        desc = change.get('short_description', '').lower()
                        if 'freeze' in desc or 'blackout' in desc or change.get('risk') == 'High':
                            conflicts.append({
                                'event': change.get('short_description', 'Scheduled Change'),
                                'start': change.get('start_date', 'N/A'),
                                'end': change.get('end_date', 'N/A'),
                                'number': change.get('number', 'N/A')
                            })
        except Exception as e:
            print(f"ServiceNow API Error: {e}")
    
    # Fallback to CSV
    if not conflicts and os.path.exists(Config.CALENDAR_FILE):
        try:
            with open(Config.CALENDAR_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        freeze_start = datetime.strptime(row['start_date'], "%Y-%m-%d")
                        freeze_end = datetime.strptime(row['end_date'], "%Y-%m-%d")
                        
                        if freeze_start <= proposed_date <= freeze_end:
                            conflicts.append({
                                'event': row['event_name'],
                                'type': row.get('event_type', 'freeze'),
                                'start': row['start_date'],
                                'end': row['end_date'],
                                'description': row.get('description', '')
                            })
                    except Exception as e:
                        print(f"CSV parsing error: {e}")
                        continue
        except Exception as e:
            print(f"CSV read error: {e}")
    
    # Format response
    if conflicts:
        warnings = ["⚠️ **Conflict Detected!**\n\n"]
        for conflict in conflicts:
            if 'number' in conflict:
                warnings.append(
                    f"- **{conflict['event']}** ({conflict.get('number')})\n"
                    f"  - Period: {conflict['start']} to {conflict['end']}\n"
                )
            else:
                warnings.append(
                    f"- **{conflict['event']}**\n"
                    f"  - Period: {conflict['start']} to {conflict['end']}\n"
                    f"  - {conflict.get('description', '')}\n"
                )
        
        warnings.append(f"\n❌ **Recommendation:** Please select a different date to avoid operational conflicts.")
        return jsonify({"answer": "".join(warnings)})
    else:
        return jsonify({
            "answer": f"✅ **No conflicts found!**\n\nThe date **{proposed_date.strftime('%B %d, %Y')}** appears to be available for scheduling your change. Please proceed with your change request."
        })
