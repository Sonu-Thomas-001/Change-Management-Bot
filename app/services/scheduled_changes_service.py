import os
import requests
import datetime
from flask import jsonify, Response
from requests.auth import HTTPBasicAuth
from app.config import Config
import urllib.parse
from app.services.export_service import generate_csv_export


def parse_time_period(query):
    """
    Parse natural language time period from query and return date range.
    
    Returns:
        tuple: (start_date, end_date, period_name, is_past)
    """
    query_lower = query.lower()
    now = datetime.datetime.now()
    today = now.date()
    
    # Helper to get date ranges
    def get_weekend():
        """Get next weekend (Saturday-Sunday)"""
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and now.hour >= 12:  # If it's Saturday afternoon, get next weekend
            days_until_saturday = 7
        saturday = today + datetime.timedelta(days=days_until_saturday)
        sunday = saturday + datetime.timedelta(days=1)
        return saturday, sunday + datetime.timedelta(hours=23, minutes=59, seconds=59)
    
    def get_month_range(offset=0):
        """Get month range. offset=0 for current month, 1 for next, -1 for previous"""
        year = now.year
        month = now.month + offset
        
        # Handle year boundaries
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        # First day of month
        start = datetime.date(year, month, 1)
        
        # Last day of month
        if month == 12:
            end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        return start, datetime.datetime.combine(end, datetime.time(23, 59, 59))
    
    # --- Dynamic Regex Parsing ---
    import re
    
    # Pattern: "last/next X days/weeks/months/years"
    # Matches: "last 5 days", "next 2 weeks", "past 3 months", "upcoming 10 days"
    match = re.search(r"(last|past|previous|next|upcoming)\s+(\d+)\s+(day|week|month|year)s?", query_lower)
    
    if match:
        direction = match.group(1) # last, next, etc.
        number = int(match.group(2))
        unit = match.group(3) # day, week, month, year
        
        is_past_direction = direction in ["last", "past", "previous"]
        
        if unit == "day":
            delta = datetime.timedelta(days=number)
        elif unit == "week":
            delta = datetime.timedelta(weeks=number)
        elif unit == "month":
            delta = datetime.timedelta(days=number * 30) # Approx
        elif unit == "year":
            delta = datetime.timedelta(days=number * 365) # Approx
            
        if is_past_direction:
            start = datetime.datetime.combine(today - delta, datetime.time(0, 0, 0))
            end = datetime.datetime.combine(today, datetime.time(23, 59, 59))
            period_name = f"Last {number} {unit.title()}s"
            return (start, end, period_name, True)
        else:
            start = datetime.datetime.combine(today, datetime.time(0, 0, 0))
            end = datetime.datetime.combine(today + delta, datetime.time(23, 59, 59))
            period_name = f"Next {number} {unit.title()}s"
            return (start, end, period_name, False)

    # --- Static Parsing Fallbacks ---
    if "last year" in query_lower or "previous year" in query_lower:
        start = datetime.datetime(now.year - 1, 1, 1)
        end = datetime.datetime(now.year - 1, 12, 31, 23, 59, 59)
        return (start, end, f"Last Year ({now.year - 1})", True)

    elif "this year" in query_lower:
        start = datetime.datetime(now.year, 1, 1)
        end = datetime.datetime(now.year, 12, 31, 23, 59, 59)
        return (start, end, f"This Year ({now.year})", False)

    elif "last months" in query_lower: # Fallback for plural without number
        start = datetime.datetime.combine(today - datetime.timedelta(days=90), datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today, datetime.time(23, 59, 59))
        return (start, end, "Last 3 Months", True)

    elif "today" in query_lower:
        start = datetime.datetime.combine(today, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today, datetime.time(23, 59, 59))
        return (start, end, "Today", False)
    
    elif "tomorrow" in query_lower:
        tomorrow = today + datetime.timedelta(days=1)
        start = datetime.datetime.combine(tomorrow, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(tomorrow, datetime.time(23, 59, 59))
        return (start, end, "Tomorrow", False)
    
    elif "weekend" in query_lower or "this weekend" in query_lower:
        start, end = get_weekend()
        start = datetime.datetime.combine(start, datetime.time(0, 0, 0))
        return (start, end, "This Weekend", False)
    
    elif "next week" in query_lower:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + datetime.timedelta(days=days_until_monday)
        next_sunday = next_monday + datetime.timedelta(days=6)
        start = datetime.datetime.combine(next_monday, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(next_sunday, datetime.time(23, 59, 59))
        return (start, end, "Next Week", False)
    
    elif "this month" in query_lower or ("month" in query_lower and "next" not in query_lower and "last" not in query_lower):
        start, end = get_month_range(0)
        start = datetime.datetime.combine(start, datetime.time(0, 0, 0))
        return (start, end, f"{now.strftime('%B %Y')}", False)
    
    elif "next month" in query_lower:
        start, end = get_month_range(1)
        start = datetime.datetime.combine(start, datetime.time(0, 0, 0))
        return (start, end, f"{(now + datetime.timedelta(days=32)).strftime('%B %Y')}", False)
    
    elif "last month" in query_lower or "previous month" in query_lower:
        start, end = get_month_range(-1)
        start = datetime.datetime.combine(start, datetime.time(0, 0, 0))
        return (start, end, f"{(now - datetime.timedelta(days=32)).strftime('%B %Y')}", True)
    
    elif "last week" in query_lower or "previous week" in query_lower:
        days_since_monday = today.weekday()
        last_monday = today - datetime.timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + datetime.timedelta(days=6)
        start = datetime.datetime.combine(last_monday, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(last_sunday, datetime.time(23, 59, 59))
        return (start, end, "Last Week", True)
    
    elif "upcoming" in query_lower or "next 7 days" in query_lower:
        start = datetime.datetime.combine(today, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today + datetime.timedelta(days=7), datetime.time(23, 59, 59))
        return (start, end, "Upcoming (Next 7 Days)", False)
    
    elif "completed" in query_lower or "closed" in query_lower:
        # Default to last 7 days for completed
        start = datetime.datetime.combine(today - datetime.timedelta(days=7), datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today, datetime.time(23, 59, 59))
        return (start, end, "Completed (Last 7 Days)", True)
    
    elif "all" in query_lower:
        # Default to a wide range: Last 1 year to Next 3 months
        start = datetime.datetime.combine(today - datetime.timedelta(days=365), datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today + datetime.timedelta(days=90), datetime.time(23, 59, 59))
        return (start, end, "All Changes (Past Year & Upcoming)", True)
    
    else:
        # Default to upcoming week
        start = datetime.datetime.combine(today, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(today + datetime.timedelta(days=7), datetime.time(23, 59, 59))
        return (start, end, "Upcoming (Next 7 Days)", False)


def extract_keywords(query):
    """
    Extract search keywords from query, removing stop words and time terms.
    """
    stop_words = [
        "show", "me", "changes", "change", "requests", "tickets", "list", "get", "find",
        "planned", "scheduled", "upcoming", "completed", "closed", "for", "the", "in", "on", "at", "from", "all",
        "today", "tomorrow", "weekend", "week", "month", "year", "next", "last", "this", "previous",
        "days", "weeks", "months", "years", "what", "are", "is", "do", "does", "did", "can", "could", "would",
        "will", "have", "has", "had", "of", "to", "a", "an", "and", "or", "but", "about"
    ]
    
    # Remove punctuation and split
    import string
    query = query.lower()
    for char in string.punctuation:
        query = query.replace(char, ' ')
        
    words = query.split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords


def export_scheduled_changes(query):
    """
    Export scheduled changes to CSV based on query.
    """
    print(f"DEBUG: Exporting scheduled changes for query: {query}")
    # Reuse the same logic to get the data
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    start_date, end_date, period_name, is_past = parse_time_period(query)
    keywords = extract_keywords(query)
    
    # Smart Date Range: If user searches for keywords but doesn't specify a date, widen the range.
    if period_name == "Upcoming (Next 7 Days)" and keywords:
        now = datetime.datetime.now()
        today = now.date()
        start_date = datetime.datetime.combine(today - datetime.timedelta(days=365), datetime.time(0, 0, 0))
        end_date = datetime.datetime.combine(today + datetime.timedelta(days=90), datetime.time(23, 59, 59))
        period_name = "All Changes (Keyword Search)"
        is_past = True

    changes = []
    
    # Mock data if ServiceNow is not configured
    if not all([INSTANCE, USER, PASSWORD]):
        # Get raw mock data (we need to bypass the HTML formatting of _get_mock_scheduled_changes)
        # So we'll call a helper that returns list instead of HTML
        changes = _get_raw_mock_data(is_past)
    else:
        # Real API call (simplified version of get_scheduled_changes)
        try:
            url = f"{INSTANCE}/api/now/table/change_request"
            start_d, start_t = start_date.strftime("%Y-%m-%d"), start_date.strftime("%H:%M:%S")
            end_d, end_t = end_date.strftime("%Y-%m-%d"), end_date.strftime("%H:%M:%S")
            
            if is_past and ("completed" in query.lower() or "closed" in query.lower()):
                sysparm_query = f"start_dateBETWEENjavascript:gs.dateGenerate('{start_d}','{start_t}')@javascript:gs.dateGenerate('{end_d}','{end_t}')^stateIN3,4,7"
            else:
                sysparm_query = f"start_dateBETWEENjavascript:gs.dateGenerate('{start_d}','{start_t}')@javascript:gs.dateGenerate('{end_d}','{end_t}')"
            
            params = {
                "sysparm_query": sysparm_query,
                "sysparm_display_value": "true",
                "sysparm_fields": "number,short_description,state,priority,risk,start_date,end_date,assigned_to",
                "sysparm_limit": 100
            }
            
            response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, timeout=10)
            if response.status_code == 200:
                changes = response.json().get('result', [])
        except Exception as e:
            print(f"Export Error: {e}. Falling back to mock data.")
            changes = _get_raw_mock_data(is_past)

    # Filter by keywords
    if keywords:
        filtered = []
        for change in changes:
            text = (change.get('short_description', '') + " " + change.get('number', '')).lower()
            if any(k in text for k in keywords):
                filtered.append(change)
        changes = filtered
        
    # Prepare data for CSV
    export_data = []
    for change in changes:
        export_data.append({
            "Number": change.get('number', ''),
            "Description": change.get('short_description', ''),
            "State": change.get('state', ''),
            "Priority": change.get('priority', ''),
            "Risk": change.get('risk', ''),
            "Start Date": change.get('start_date', ''),
            "End Date": change.get('end_date', ''),
            "Assigned To": change.get('assigned_to', '')
        })
        
    filename = f"changes_{period_name.replace(' ', '_')}.csv"
    return generate_csv_export(export_data, filename)


def get_scheduled_changes(query):
    """
    Fetch scheduled or completed changes from ServiceNow based on time period in query.
    Falls back to mock data if ServiceNow is not configured.
    
    Args:
        query (str): User's natural language query
        
    Returns:
        flask.Response: JSON response with HTML table of changes
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    # Parse time period
    start_date, end_date, period_name, is_past = parse_time_period(query)
    keywords = extract_keywords(query)
    
    # Smart Date Range: If user searches for keywords (e.g., "firewall") but doesn't specify a date,
    # default to a wide range (Past Year + Future) instead of just "Next 7 Days".
    if period_name == "Upcoming (Next 7 Days)" and keywords:
        now = datetime.datetime.now()
        today = now.date()
        start_date = datetime.datetime.combine(today - datetime.timedelta(days=365), datetime.time(0, 0, 0))
        end_date = datetime.datetime.combine(today + datetime.timedelta(days=90), datetime.time(23, 59, 59))
        period_name = "All Changes (Keyword Search)"
        is_past = True # Enable past search logic
    
    # Mock data if ServiceNow is not configured
    if not all([INSTANCE, USER, PASSWORD]):
        return _get_mock_scheduled_changes(period_name, is_past, keywords)
    
    # Real ServiceNow API call
    try:
        url = f"{INSTANCE}/api/now/table/change_request"
        
        # Format dates for ServiceNow query
        start_d, start_t = start_date.strftime("%Y-%m-%d"), start_date.strftime("%H:%M:%S")
        end_d, end_t = end_date.strftime("%Y-%m-%d"), end_date.strftime("%H:%M:%S")
        
        # Build query based on whether we want past or future changes
        # Only filter by "Closed/Completed" state if explicitly requested
        if is_past and ("completed" in query.lower() or "closed" in query.lower()):
            sysparm_query = f"start_dateBETWEENjavascript:gs.dateGenerate('{start_d}','{start_t}')@javascript:gs.dateGenerate('{end_d}','{end_t}')^stateIN3,4,7"
        else:
            sysparm_query = f"start_dateBETWEENjavascript:gs.dateGenerate('{start_d}','{start_t}')@javascript:gs.dateGenerate('{end_d}','{end_t}')"
        
        # Add keyword search if keywords are present
        if keywords:
            search_term = " ".join(keywords)
            sysparm_query += f"^123TEXTQUERY321={search_term}"
            
        params = {
            "sysparm_query": sysparm_query,
            "sysparm_display_value": "true",
            "sysparm_fields": "number,short_description,state,priority,risk,start_date,end_date,assigned_to",
            "sysparm_limit": 50,
            "sysparm_order_by": "start_date"
        }
        
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            changes = data.get('result', [])
            
            if not changes:
                msg = f"✅ No changes found for **{period_name}**"
                if keywords:
                    msg += f" matching keywords: **{', '.join(keywords)}**"
                return jsonify({"answer": msg + "."})

            return _format_changes_table(changes, period_name, is_past, query, is_mock=False)
        else:
            print(f"ServiceNow API Error: Status {response.status_code}")
            return _get_mock_scheduled_changes(period_name, is_past)
            
    except Exception as e:
        print(f"Error fetching scheduled changes: {e}")
        return _get_mock_scheduled_changes(period_name, is_past)


def _get_raw_mock_data(is_past):
    """Helper to get raw mock data list"""
    now = datetime.datetime.now()
    if is_past:
        return [
            {
                "number": "CHG0030001",
                "short_description": "Database Backup Verification",
                "state": "Closed",
                "priority": "3 - Moderate",
                "risk": "Low",
                "start_date": (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d 02:00:00"),
                "end_date": (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d 04:00:00"),
                "assigned_to": "John Smith"
            },
            {
                "number": "CHG0030002",
                "short_description": "Security Patch Deployment - Web Servers",
                "state": "Closed",
                "priority": "2 - High",
                "risk": "Medium",
                "start_date": (now - datetime.timedelta(days=5)).strftime("%Y-%m-%d 22:00:00"),
                "end_date": (now - datetime.timedelta(days=4)).strftime("%Y-%m-%d 02:00:00"),
                "assigned_to": "Sarah Johnson"
            }
        ]
    else:
        return [
            {
                "number": "CHG0040001",
                "short_description": "Network Switch Upgrade - Building A",
                "state": "Scheduled",
                "priority": "2 - High",
                "risk": "Medium",
                "start_date": (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 20:00:00"),
                "end_date": (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:00:00"),
                "assigned_to": "Mike Davis"
            },
            {
                "number": "CHG0040002",
                "short_description": "Oracle Database Upgrade - Production",
                "state": "Authorize",
                "priority": "1 - Critical",
                "risk": "High",
                "start_date": (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d 01:00:00"),
                "end_date": (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d 06:00:00"),
                "assigned_to": "David Lee"
            },
            {
                "number": "CHG0040003",
                "short_description": "Firewall Rule Update - DMZ",
                "state": "Scheduled",
                "priority": "3 - Moderate",
                "risk": "Low",
                "start_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d 14:00:00"),
                "end_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d 15:00:00"),
                "assigned_to": "Lisa Wong"
            }
        ]

def _get_mock_scheduled_changes(period_name, is_past, keywords=None):
    """Generate mock data for scheduled changes"""
    mock_changes = _get_raw_mock_data(is_past)
    
    # Filter by keywords
    if keywords:
        filtered = []
        for change in mock_changes:
            text = (change.get('short_description', '') + " " + change.get('number', '')).lower()
            if any(k in text for k in keywords):
                filtered.append(change)
        mock_changes = filtered
        
        if not mock_changes:
             return jsonify({
                "answer": f"✅ No changes found for **{period_name}** matching keywords: **{', '.join(keywords)}** (Demo Data)."
            })
    
    return _format_changes_table(mock_changes, period_name, is_past, f"changes {period_name}", is_mock=True)


def _format_changes_table(changes, period_name, is_past, query_text, is_mock=False):
    """Format changes data as HTML table"""
    
    if "completed" in query_text.lower() or "closed" in query_text.lower():
        status_text = "Completed"
    elif "all" in query_text.lower():
        status_text = "All"
    elif is_past:
        status_text = "Past"
    else:
        status_text = "Scheduled"
    mock_note = " (Demo Data)" if is_mock else ""
    
    # URL encode the query for the export link
    encoded_query = urllib.parse.quote(query_text)
    export_link = f"/export_changes?query={encoded_query}"
    
    table_html = f'''<div class="changes-container">
        <div style="display: flex; justify-content: space-between; align_items: center; margin-bottom: 10px;">
            <h3 style="margin: 0;">📅 {status_text} Changes for {period_name}{mock_note}</h3>
        </div>
        <p style="color: #666; margin-bottom: 15px;">Found <strong>{len(changes)}</strong> change request(s)</p>
        <div class="table-responsive">
            <table class="changes-table">
                <thead>
                    <tr>
                        <th>Number</th>
                        <th>Description</th>
                        <th>State</th>
                        <th>Priority</th>
                        <th>Start Time</th>
                        <th>End Time</th>
                        <th>Assigned To</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    for change in changes:
        number = change.get('number', 'N/A')
        desc = change.get('short_description', 'No description')
        state = change.get('state', 'N/A')
        priority = change.get('priority', 'N/A')
        start = change.get('start_date', 'N/A')
        end = change.get('end_date', 'N/A')
        assigned = change.get('assigned_to', 'Unassigned')
        
        # Handle case where assigned_to is a dictionary (ServiceNow reference object)
        if isinstance(assigned, dict):
            assigned = assigned.get('display_value', assigned.get('name', 'Unassigned'))
        
        # Determine state badge color
        state_class = "state-scheduled"
        if "closed" in str(state).lower() or "complete" in str(state).lower():
            state_class = "state-closed"
        elif "implement" in str(state).lower():
            state_class = "state-implement"
        elif "authorize" in str(state).lower():
            state_class = "state-authorize"
        
        # Determine priority badge
        priority_num = str(priority).split()[0] if priority != 'N/A' else '4'
        priority_class = f"priority-{priority_num}"
        
        table_html += f'''
                <tr>
                    <td><strong>{number}</strong></td>
                    <td>{desc[:80]}{'...' if len(desc) > 80 else ''}</td>
                    <td><span class="state-badge {state_class}">{state}</span></td>
                    <td><span class="priority-badge {priority_class}">{priority}</span></td>
                    <td>{start}</td>
                    <td>{end}</td>
                    <td>{assigned}</td>
                </tr>
        '''
    
    table_html += f'''
                </tbody>
            </table>
        </div>
        <div style="margin-top: 15px;">
            <a href="{export_link}" target="_blank" class="export-btn">📊 Export to Excel</a>
        </div>
    </div>
    '''
    
    table_html += '''
    <style>
        .changes-container { margin: 10px 0; }
        .changes-container h3 { margin-bottom: 5px; color: #333; }
        .table-responsive { overflow-x: auto; margin-top: 15px; }
        .changes-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; font-size: 0.9rem; }
        .changes-table th { background: #031f4a; color: white; padding: 12px 10px; text-align: left; font-weight: 600; }
        .changes-table td { padding: 10px; border-bottom: 1px solid #e0e0e0; }
        .changes-table tr:hover { background: #f8f9fa; }
        .state-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
        .state-scheduled { background: #17a2b8; color: white; }
        .state-implement { background: #007bff; color: white; }
        .state-authorize { background: #ffc107; color: #333; }
        .state-closed { background: #28a745; color: white; }
        .priority-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
        .priority-1 { background: #dc3545; color: white; }
        .priority-2 { background: #fd7e14; color: white; }
        .priority-3 { background: #ffc107; color: #333; }
        .priority-4 { background: #28a745; color: white; }
        .export-btn { 
            background-color: #28a745; 
            color: white; 
            padding: 8px 15px; 
            text-decoration: none; 
            border-radius: 5px; 
            font-weight: bold; 
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: background-color 0.2s;
        }
        .export-btn:hover { background-color: #218838; }
    </style>
    '''
    
    return jsonify({"answer": table_html, "disable_copy": True})
