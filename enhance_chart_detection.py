# Script to enhance chart query detection in app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the chart detection section
old_code = '''    # 6. Enhanced Chart/Stats Intent  
    if any(x in lower_q for x in ["chart", "graph", "stats", "breakdown", "metrics", "trend", "workload"]):'''

new_code = '''    # 6. Enhanced Chart/Stats Intent  
    chart_keywords = ["chart", "graph", "stats", "breakdown", "metrics", "trend", "workload", "how many", "show", "display", "visualize"]
    if any(x in lower_q for x in chart_keywords):'''

content = content.replace(old_code, new_code)

# Replace the approval detection logic
old_approval = '''        elif "approval" in lower_q or "approved" in lower_q or "rejected" in lower_q:
            return get_servicenow_stats(group_by_field="approval_rate", chart_type="doughnut")'''

new_approval = '''        elif any(word in lower_q for word in ["approval", "approved", "rejected", "reject", "accept", "accepted", "deny", "denied"]):
            # Check if asking for comparison or counts
            if any(word in lower_q for word in ["vs", "versus", "compared", "comparison"]):
                return get_servicenow_stats(group_by_field="approval_rate", chart_type="pie")
            return get_servicenow_stats(group_by_field="approval_rate", chart_type="doughnut")'''

content = content.replace(old_approval, new_approval)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully enhanced chart query detection in app.py")
