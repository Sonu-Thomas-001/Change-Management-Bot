import os
import requests
from flask import jsonify
from requests.auth import HTTPBasicAuth
from app.config import Config

def get_servicenow_stats(group_by_field="state", chart_type="bar"):
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        mock_map = {
            "risk": {"labels": ["Very High", "High", "Moderate", "Low"], "data": [2, 5, 15, 30]},
            "priority": {"labels": ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"], "data": [1, 4, 20, 10]},
            "category": {"labels": ["Hardware", "Software", "Network", "Database", "Security"], "data": [12, 25, 8, 5, 10]},
            "state": {"labels": ["New", "Assess", "Authorize", "Scheduled", "Implement", "Closed"], "data": [10, 5, 8, 12, 15, 40]},
            "assignee": {"labels": ["John D.", "Sarah M.", "Mike R.", "Lisa K.", "David L."], "data": [15, 20, 12, 8, 10]},
            "change_type": {"labels": ["Standard", "Normal", "Emergency", "Expedited"], "data": [30, 20, 5, 10]},
            "approval_rate": {"labels": ["Approved", "Rejected", "Pending"], "data": [45, 8, 12]},
            "monthly_trend": {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "data": [25, 30, 28, 35, 40, 38]},
            "completion_time": {"labels": ["< 1 day", "1-3 days", "3-7 days", "7-14 days", "> 14 days"], "data": [10, 25, 20, 15, 5]},
            "impact": {"labels": ["1 - High", "2 - Medium", "3 - Low"], "data": [8, 22, 35]},
            "assignment_group": {"labels": ["Network Team", "Database Team", "App Team", "Security Team", "Infrastructure"], "data": [15, 12, 20, 8, 10]}
        }
        selected_data = mock_map.get(group_by_field, mock_map["state"])
        
        return jsonify({
            "type": "chart",
            "text": f"Here is the breakdown of Change Requests by **{group_by_field.upper()}**:",
            "chart_type": chart_type,
            "chart_data": {
                "labels": selected_data["labels"],
                "datasets": [{
                    "label": f"Changes by {group_by_field}",
                    "data": selected_data["data"],
                    "backgroundColor": ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2'],
                    "borderWidth": 1
                }]
            }
        })

    url = f"{INSTANCE}/api/now/stats/change_request"
    params = {
        "sysparm_count": "true",
        "sysparm_group_by": group_by_field,
        "sysparm_display_value": "true"
    }
    
    try:
        headers = {"Accept": "application/json"}
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"ServiceNow Stats API Error: {response.status_code} - {response.text[:200]}")
            raise Exception(f"API returned status {response.status_code}")

        if not response.text.strip():
            print(f"ServiceNow Stats API returned empty response. Content-Type: {response.headers.get('Content-Type')}")
            raise Exception("API returned empty response")

        try:
            data = response.json()
        except ValueError:
            print(f"ServiceNow Stats API Invalid JSON: {response.text[:200]}")
            raise Exception("API returned invalid JSON")
        labels = []
        counts = []
        if 'result' in data:
            for group in data['result']:
                val = group['groupby_fields'][0]['value']
                count = int(group['stats']['count'])
                if count > 0:
                    labels.append(val if val else "Unknown")
                    counts.append(count)
        
        return jsonify({
            "type": "chart",
            "text": f"Found {sum(counts)} tickets grouped by **{group_by_field}**:",
            "chart_type": chart_type,
            "chart_data": {
                "labels": labels,
                "datasets": [{
                    "label": f"Changes by {group_by_field}",
                    "data": counts,
                    "backgroundColor": ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2'],
                    "borderWidth": 1
                }]
            }
        })
    except Exception as e:
        print(f"API Error: {e}. Falling back to mock data.")
        # Fallback to mock data on API error
        mock_map = {
            "risk": {"labels": ["Very High", "High", "Moderate", "Low"], "data": [2, 5, 15, 30]},
            "priority": {"labels": ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"], "data": [1, 4, 20, 10]},
            "category": {"labels": ["Hardware", "Software", "Network", "Database", "Security"], "data": [12, 25, 8, 5, 10]},
            "state": {"labels": ["New", "Assess", "Authorize", "Scheduled", "Implement", "Closed"], "data": [10, 5, 8, 12, 15, 40]},
            "assignee": {"labels": ["John D.", "Sarah M.", "Mike R.", "Lisa K.", "David L."], "data": [15, 20, 12, 8, 10]},
            "change_type": {"labels": ["Standard", "Normal", "Emergency", "Expedited"], "data": [30, 20, 5, 10]},
            "approval_rate": {"labels": ["Approved", "Rejected", "Pending"], "data": [45, 8, 12]},
            "monthly_trend": {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "data": [25, 30, 28, 35, 40, 38]},
            "completion_time": {"labels": ["< 1 day", "1-3 days", "3-7 days", "7-14 days", "> 14 days"], "data": [10, 25, 20, 15, 5]},
            "impact": {"labels": ["1 - High", "2 - Medium", "3 - Low"], "data": [8, 22, 35]},
            "assignment_group": {"labels": ["Network Team", "Database Team", "App Team", "Security Team", "Infrastructure"], "data": [15, 12, 20, 8, 10]}
        }
        selected_data = mock_map.get(group_by_field, mock_map["state"])
        
        return jsonify({
            "type": "chart",
            "text": f"Here is the breakdown of Change Requests by **{group_by_field.upper()}** (Demo Data):",
            "chart_type": chart_type,
            "chart_data": {
                "labels": selected_data["labels"],
                "datasets": [{
                    "label": f"Changes by {group_by_field}",
                    "data": selected_data["data"],
                    "backgroundColor": ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2'],
                    "borderWidth": 1
                }]
            }
        })



def create_change_request(description, impact="Low", risk="Low"):
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        import random
        new_id = f"CR-{random.randint(2000, 9999)}"
        return jsonify({"answer": f"✅ Successfully created draft Change Request **{new_id}**.\n\n*Description:* {description}\n*Impact:* {impact}\n*Risk:* {risk}"})

    url = f"{INSTANCE}/api/now/table/change_request"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "short_description": description,
        "impact": "3" if impact == "Low" else "1",
        "risk": "3" if risk == "Low" else "1",
        "state": "-5"
    }

    try:
        response = requests.post(url, auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            new_number = data['result']['number']
            return jsonify({"answer": f"✅ Created Change Request **{new_number}** in ServiceNow."})
        else:
            return jsonify({"answer": f"Failed to create ticket. Status: {response.status_code}"})
    except Exception as e:
        return jsonify({"answer": f"API Error: {str(e)}"})

def create_change_request_raw(description, impact="Low", risk="Low"):
    """
    Creates a new change request and returns the raw data dict.
    Returns: {"status": "success", "data": {...}} or {"status": "error", "message": "..."}
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        import random
        new_id = f"CR-{random.randint(2000, 9999)}"
        return {
            "status": "success",
            "data": {
                "number": new_id,
                "short_description": description,
                "description": description,
                "risk": risk,
                "impact": impact,
                "type": "Normal",
                "priority": "4 - Low",
                "assignment_group": "Service Desk"
            }
        }

    url = f"{INSTANCE}/api/now/table/change_request"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "short_description": description,
        "impact": "3" if impact == "Low" else "1",
        "risk": "3" if risk == "Low" else "1",
        "state": "-5"
    }
    
    # Add sysparm_fields to get more details back
    params = {
        "sysparm_fields": "number,short_description,description,risk,impact,type,priority,assignment_group,sys_id",
        "sysparm_display_value": "true"
    }

    try:
        response = requests.post(url, auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, json=payload, params=params)
        if response.status_code == 201:
            data = response.json()
            return {"status": "success", "data": data['result']}
        else:
            return {"status": "error", "message": f"Failed to create ticket. Status: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"API Error: {str(e)}"}



def get_pending_approvals():
    """
    Fetch pending approvals from ServiceNow and return as formatted HTML table
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    # Mock data if ServiceNow is not configured
    if not all([INSTANCE, USER, PASSWORD]):
        mock_approvals = [
            {
                "number": "SCTASK0010001",
                "short_description": "Approve Server Upgrade for Production",
                "requested_by": "John Smith",
                "opened_at": "2025-11-20 10:30:00",
                "priority": "2 - High",
                "state": "Pending Approval"
            },
            {
                "number": "SCTASK0010002",
                "short_description": "Database Migration - Customer Portal",
                "requested_by": "Sarah Johnson",
                "opened_at": "2025-11-21 14:15:00",
                "priority": "1 - Critical",
                "state": "Pending Approval"
            },
            {
                "number": "SCTASK0010003",
                "short_description": "Network Configuration Change",
                "requested_by": "Mike Davis",
                "opened_at": "2025-11-22 09:00:00",
                "priority": "3 - Moderate",
                "state": "Pending Approval"
            }
        ]
        
        # Build HTML table
        table_html = '''
        <div class="approvals-container">
            <h3>📋 Your Pending Approvals</h3>
            <div class="table-responsive">
                <table class="approvals-table">
                    <thead>
                        <tr>
                            <th>Ticket</th>
                            <th>Description</th>
                            <th>Requested By</th>
                            <th>Priority</th>
                            <th>Opened</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for approval in mock_approvals:
            table_html += f'''
                        <tr>
                            <td><strong>{approval['number']}</strong></td>
                            <td>{approval['short_description']}</td>
                            <td>{approval['requested_by']}</td>
                            <td><span class="priority-badge priority-{approval['priority'].split()[0]}">{approval['priority']}</span></td>
                            <td>{approval['opened_at']}</td>
                            <td><button class="view-btn" onclick="window.open('#{approval['number']}', '_blank')">View</button></td>
                        </tr>
            '''
        
        table_html += '''
                    </tbody>
                </table>
            </div>
        </div>
        <style>
            .approvals-container { margin: 10px 0; }
            .approvals-container h3 { margin-bottom: 15px; color: #333; }
            .table-responsive { overflow-x: auto; }
            .approvals-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
            .approvals-table th { background: #031f4a; color: white; padding: 12px; text-align: left; font-weight: 600; }
            .approvals-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; }
            .approvals-table tr:hover { background: #f8f9fa; }
            .priority-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
            .priority-1 { background: #dc3545; color: white; }
            .priority-2 { background: #fd7e14; color: white; }
            .priority-3 { background: #ffc107; color: #333; }
            .priority-4 { background: #28a745; color: white; }
            .view-btn { background: #007bff; color: white; border: none; padding: 6px 16px; border-radius: 4px; cursor: pointer; font-weight: 500; transition: all 0.2s; }
            .view-btn:hover { background: #0056b3; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        </style>
        '''
        
        return jsonify({"answer": table_html, "disable_copy": True})
    
    # Real ServiceNow API call
    try:
        # Resolve User Sys ID first
        # Per user request: Always fetch pending approvals for "david.loo"
        target_user = "david.loo"
        
        user_sys_id = None
        user_url = f"{INSTANCE}/api/now/table/sys_user"
        user_params = {"sysparm_query": f"user_name={target_user}", "sysparm_fields": "sys_id", "sysparm_limit": 1}
        u_resp = requests.get(user_url, auth=HTTPBasicAuth(USER, PASSWORD), params=user_params)
        if u_resp.status_code == 200:
            results = u_resp.json().get('result', [])
            if results:
                user_sys_id = results[0]['sys_id']
        
        if not user_sys_id:
             # Fallback to username if sys_id lookup fails
             print(f"⚠️ Could not resolve sys_id for {target_user}, using username.")
             user_sys_id = target_user

        url = f"{INSTANCE}/api/now/table/sysapproval_approver"
        params = {
            "sysparm_query": f"approver={user_sys_id}^state=requested",
            "sysparm_display_value": "true",
            "sysparm_fields": "sysapproval.number,sysapproval.short_description,state,sys_created_on,sysapproval.priority,sysapproval.risk,sysapproval.start_date,sysapproval.category,sysapproval.type",
            "sysparm_limit": 20
        }
        
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            approvals = data.get('result', [])
            
            if not approvals:
                return jsonify({"answer": "✅ You have no pending approvals at the moment!"})
            
            # Build HTML table with real data
            table_html = '''
            <div class="approvals-container">
                <h3>📋 Your Pending Approvals ({count})</h3>
                <div class="table-responsive">
                    <table class="approvals-table">
                        <thead>
                            <tr>
                                <th>Ticket</th>
                                <th>Description</th>
                                <th>Priority</th>
                                <th>Risk</th>
                                <th>Start Date</th>
                                <th>Category</th>
                                <th>Type</th>
                                <th>State</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
            '''.replace('{count}', str(len(approvals)))
            
            for approval in approvals:
                number = approval.get('sysapproval.number', 'N/A')
                desc = approval.get('sysapproval.short_description', 'No description')
                priority = approval.get('sysapproval.priority', 'N/A')
                risk = approval.get('sysapproval.risk', 'N/A')
                start_date = approval.get('sysapproval.start_date', 'N/A')
                category = approval.get('sysapproval.category', 'N/A')
                chg_type = approval.get('sysapproval.type', 'N/A')
                state = approval.get('state', 'N/A')
                
                table_html += f'''
                            <tr>
                                <td><strong>{number}</strong></td>
                                <td>{desc}</td>
                                <td>{priority}</td>
                                <td>{risk}</td>
                                <td>{start_date}</td>
                                <td>{category}</td>
                                <td>{chg_type}</td>
                                <td><span class="state-badge">{state}</span></td>
                                <td><button class="view-btn" onclick="window.open('{INSTANCE}/sysapproval_approver.do?sysparm_query=sysapproval.number={number}', '_blank')">View</button></td>
                            </tr>
                '''
            
            table_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            <style>
                .approvals-container { margin: 10px 0; }
                .approvals-container h3 { margin-bottom: 15px; color: #333; }
                .table-responsive { overflow-x: auto; }
                .approvals-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
                .approvals-table th { background: #031f4a; color: white; padding: 12px; text-align: left; font-weight: 600; }
                .approvals-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; }
                .approvals-table tr:hover { background: #f8f9fa; }
                .state-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; background: #ffc107; color: #333; }
                .view-btn { background: #007bff; color: white; border: none; padding: 6px 16px; border-radius: 4px; cursor: pointer; font-weight: 500; transition: all 0.2s; }
                .view-btn:hover { background: #0056b3; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
            </style>
            '''
            
            return jsonify({"answer": table_html, "disable_copy": True})
        else:
            return jsonify({"answer": f"❌ Error fetching approvals: Status {response.status_code}"})
            
    except Exception as e:
        print(f"Error fetching approvals: {e}")
        return jsonify({"answer": f"❌ Error connecting to ServiceNow: {str(e)}"})


def get_pending_tasks():
    """
    Fetch pending tasks assigned to the user from ServiceNow and return as formatted HTML table
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD
    
    # Mock data if ServiceNow is not configured
    if not all([INSTANCE, USER, PASSWORD]):
        mock_tasks = [
            {
                "number": "TASK0010001",
                "short_description": "Update Configuration for Production Server",
                "state": "Work in Progress",
                "priority": "2 - High",
                "opened_at": "2025-11-20 09:00:00",
                "due_date": "2025-11-25"
            },
            {
                "number": "TASK0010002",
                "short_description": "Verify Database Backup Completion",
                "state": "Pending",
                "priority": "1 - Critical",
                "opened_at": "2025-11-22 11:30:00",
                "due_date": "2025-11-24"
            },
            {
                "number": "TASK0010003",
                "short_description": "Document Change Procedure",
                "state": "Assigned",
                "priority": "3 - Moderate",
                "opened_at": "2025-11-23 14:00:00",
                "due_date": "2025-11-26"
            },
            {
                "number": "TASK0010004",
                "short_description": "Review Security Patches",
                "state": "Pending",
                "priority": "2 - High",
                "opened_at": "2025-11-24 08:15:00",
                "due_date": "2025-11-25"
            }
        ]
        
        # Build HTML table
        table_html = '''
        <div class="tasks-container">
            <h3>📝 Your Pending Tasks</h3>
            <div class="table-responsive">
                <table class="tasks-table">
                    <thead>
                        <tr>
                            <th>Task Number</th>
                            <th>Description</th>
                            <th>State</th>
                            <th>Priority</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for task in mock_tasks:
            # Determine state badge color
            state_class = "state-pending"
            if "progress" in task['state'].lower():
                state_class = "state-progress"
            elif task['state'].lower() == "assigned":
                state_class = "state-assigned"
            
            table_html += f'''
                        <tr>
                            <td><strong>{task['number']}</strong></td>
                            <td>{task['short_description']}</td>
                            <td><span class="state-badge {state_class}">{task['state']}</span></td>
                            <td><span class="priority-badge priority-{task['priority'].split()[0]}">{task['priority']}</span></td>
                            <td><button class="view-btn" onclick="window.open('#{task['number']}', '_blank')">View</button></td>
                        </tr>
            '''
        
        table_html += '''
                    </tbody>
                </table>
            </div>
        </div>
        <style>
            .tasks-container { margin: 10px 0; }
            .tasks-container h3 { margin-bottom: 15px; color: #333; }
            .table-responsive { overflow-x: auto; }
            .tasks-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
            .tasks-table th { background: #031f4a; color: white; padding: 12px; text-align: left; font-weight: 600; }
            .tasks-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; }
            .tasks-table tr:hover { background: #f8f9fa; }
            .state-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
            .state-pending { background: #ffc107; color: #333; }
            .state-progress { background: #17a2b8; color: white; }
            .state-assigned { background: #6c757d; color: white; }
            .priority-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
            .priority-1 { background: #dc3545; color: white; }
            .priority-2 { background: #fd7e14; color: white; }
            .priority-3 { background: #ffc107; color: #333; }
            .priority-4 { background: #28a745; color: white; }
            .view-btn { background: #007bff; color: white; border: none; padding: 6px 16px; border-radius: 4px; cursor: pointer; font-weight: 500; transition: all 0.2s; }
            .view-btn:hover { background: #0056b3; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        </style>
        '''
        
        return jsonify({"answer": table_html, "disable_copy": True})
    
    # Real ServiceNow API call
    try:
        # Resolve User Sys ID first (if not already done, but we can't share scope easily here without refactoring)
        # Ideally we should have a helper, but for now duplicating the lookup is safer than refactoring the whole file
        user_sys_id = None
        user_url = f"{INSTANCE}/api/now/table/sys_user"
        user_params = {"sysparm_query": f"user_name={USER}", "sysparm_fields": "sys_id", "sysparm_limit": 1}
        u_resp = requests.get(user_url, auth=HTTPBasicAuth(USER, PASSWORD), params=user_params)
        if u_resp.status_code == 200:
            results = u_resp.json().get('result', [])
            if results:
                user_sys_id = results[0]['sys_id']
        
        if not user_sys_id:
             user_sys_id = USER

        url = f"{INSTANCE}/api/now/table/sc_task"
        params = {
            "sysparm_query": f"assigned_to={user_sys_id}^active=true^state!=3^state!=4^state!=7",
            "sysparm_display_value": "true",
            "sysparm_fields": "number,short_description,state,priority,opened_at",
            "sysparm_limit": 20,
            "sysparm_order_by": "priority"
        }
        
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('result', [])
            
            if not tasks:
                return jsonify({"answer": "✅ You have no pending tasks at the moment!"})
            
            # Build HTML table with real data
            table_html = f'''
            <div class="tasks-container">
                <h3>📝 Your Pending Tasks ({len(tasks)})</h3>
                <div class="table-responsive">
                    <table class="tasks-table">
                        <thead>
                            <tr>
                                <th>Task Number</th>
                                <th>Description</th>
                                <th>State</th>
                                <th>Priority</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            
            for task in tasks:
                number = task.get('number', 'N/A')
                desc = task.get('short_description', 'No description')
                state = task.get('state', 'N/A')
                priority = task.get('priority', 'N/A')
                due_date = task.get('due_date', 'No due date')
                
                # Determine state color
                state_class = "state-pending"
                if "progress" in state.lower():
                    state_class = "state-progress"
                elif "assigned" in state.lower():
                    state_class = "state-assigned"
                
                table_html += f'''
                            <tr>
                                <td><strong>{number}</strong></td>
                                <td>{desc}</td>
                                <td><span class="state-badge {state_class}">{state}</span></td>
                                <td><span class="priority-badge">{priority}</span></td>
                                <td><button class="view-btn" onclick="window.open('{INSTANCE}/sc_task.do?sysparm_query=number={number}', '_blank')">View</button></td>
                            </tr>
                '''
            
            table_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            <style>
                .tasks-container { margin: 10px 0; }
                .tasks-container h3 { margin-bottom: 15px; color: #333; }
                .table-responsive { overflow-x: auto; }
                .tasks-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
                .tasks-table th { background: #031f4a; color: white; padding: 12px; text-align: left; font-weight: 600; }
                .tasks-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; }
                .tasks-table tr:hover { background: #f8f9fa; }
                .state-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
                .state-pending { background: #ffc107; color: #333; }
                .state-progress { background: #17a2b8; color: white; }
                .state-assigned { background: #6c757d; color: white; }
                .priority-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; background: #6c757d; color: white; }
                .view-btn { background: #007bff; color: white; border: none; padding: 6px 16px; border-radius: 4px; cursor: pointer; font-weight: 500; transition: all 0.2s; }
                .view-btn:hover { background: #0056b3; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
            </style>
            '''
            
            return jsonify({"answer": table_html, "disable_copy": True})
        else:
            return jsonify({"answer": f"❌ Error fetching tasks: Status {response.status_code}"})
            
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return jsonify({"answer": f"❌ Error connecting to ServiceNow: {str(e)}"})

def get_recent_changes_by_keyword(keyword, limit=3):
    """
    Fetch recent changes that match a specific keyword in their description.
    """
    INSTANCE = Config.SERVICENOW_INSTANCE
    USER = Config.SERVICENOW_USER
    PASSWORD = Config.SERVICENOW_PASSWORD

    if not all([INSTANCE, USER, PASSWORD]):
        # Mock Data
        import random
        mock_changes = []
        for i in range(limit):
            num = f"CHG{random.randint(100000, 999999)}"
            mock_changes.append({
                "number": num,
                "short_description": f"Previous {keyword} implementation for {random.choice(['Production', 'UAT', 'Dev'])}",
                "state": "Closed"
            })
        return mock_changes

    url = f"{INSTANCE}/api/now/table/change_request"
    params = {
        "sysparm_query": f"short_descriptionLIKE{keyword}", # Any state
        "sysparm_fields": "number,short_description,state",
        "sysparm_limit": limit,
        "sysparm_order_by_desc": "sys_updated_on"
    }

    try:
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('result', [])
        else:
            print(f"Error fetching recent changes: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching recent changes: {e}")
        return []
