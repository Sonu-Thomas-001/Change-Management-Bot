# Script to fix ServiceNow stats function to return mock data on error
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the error handling to return mock data instead
old_error_handling = '''    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"answer": "Error fetching data from ServiceNow."})'''

new_error_handling = '''    except Exception as e:
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
        })'''

content = content.replace(old_error_handling, new_error_handling)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully fixed ServiceNow stats function to use mock data fallback")
