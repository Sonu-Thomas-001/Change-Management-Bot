import re

def validate_emergency_change(text):
    """
    Validates an emergency change request against SOP rules.
    
    Args:
        text (str): The user's input text describing the change.
        
    Returns:
        dict: A dictionary containing 'valid' (bool) and 'message' (str).
    """
    
    # 1. Justification Check
    # Look for keywords indicating a true emergency
    emergency_keywords = ["production down", "outage", "critical failure", "security breach", "data loss", "sev1", "p1"]
    if not any(keyword in text.lower() for keyword in emergency_keywords):
        return {
            "valid": False,
            "message": "❌ Blocked: Your justification is too vague for an Emergency change. Please add details about the business impact (e.g., 'Production Down', 'Critical Failure')."
        }

    # 2. Field Completeness Check
    # We expect the user to provide "Rollback Plan" and "Risk Impact" sections.
    # Simple parsing: look for "Rollback Plan:" and "Risk Impact:"
    
    # Normalize text to lower case for searching, but keep original for counting
    lower_text = text.lower()
    
    rollback_start = lower_text.find("rollback plan")
    risk_start = lower_text.find("risk impact")
    
    if rollback_start == -1:
        return {
            "valid": False,
            "message": "❌ Blocked: Missing 'Rollback Plan'. Please specify a rollback plan."
        }
        
    if risk_start == -1:
        return {
            "valid": False,
            "message": "❌ Blocked: Missing 'Risk Impact'. Please specify the risk impact."
        }
        
    # Extract content
    # Assuming the sections are separated by newlines or other headers.
    # We'll just take the text after the header until the next header or end of string.
    
    # Sort indices to know which comes first
    indices = sorted([rollback_start, risk_start])
    
    # Helper to extract text between indices
    def extract_section(start_idx, next_idx=None):
        # Add length of header (approximate, "rollback plan" is 13 chars)
        # We'll just split by the header string to be safer
        pass 

    # Let's use regex for better extraction
    # Pattern: Look for "Rollback Plan[:\s-]" ... until "Risk Impact" or end
    
    # A more robust way given it's natural language might be just checking the length of the whole input 
    # if we can't parse perfectly, but let's try to be specific as requested.
    
    # Let's try to split the text by these keys
    # Note: This is a simple parser. In a real app, we might use an LLM or structured form.
    
    # We will assume the user types: "Rollback Plan: ... Risk Impact: ..."
    
    # logic: split by keywords
    parts = re.split(r'(rollback plan[:\s-]|risk impact[:\s-])', text, flags=re.IGNORECASE)
    
    # parts[0] is pre-text, parts[1] is first delimiter, parts[2] is first content, etc.
    # This is getting complicated to map back.
    
    # Simpler approach:
    # Find the substring after "Rollback Plan"
    rollback_content = text[rollback_start+13:] # 13 is len("rollback plan")
    # If risk is after rollback, cut it off
    if risk_start > rollback_start:
        rollback_content = text[rollback_start+13:risk_start]
    
    # Find substring after "Risk Impact"
    risk_content = text[risk_start+11:] # 11 is len("risk impact")
    # If rollback is after risk, cut it off
    if rollback_start > risk_start:
        risk_content = text[risk_start+11:rollback_start]
        
    # Count words
    rollback_words = len(rollback_content.split())
    risk_words = len(risk_content.split())
    
    if rollback_words < 10:
        return {
            "valid": False,
            "message": f"❌ Blocked: 'Rollback Plan' is too short ({rollback_words} words). Minimum 10 words required."
        }
        
    if risk_words < 10:
        return {
            "valid": False,
            "message": f"❌ Blocked: 'Risk Impact' is too short ({risk_words} words). Minimum 10 words required."
        }

    # 3. Approval Route Check
    # Check for "ECAB" or "CAB" or specific roles
    approver_keywords = ["ecab", "emergency cab", "cab", "manager", "director", "vp"]
    if not any(keyword in text.lower() for keyword in approver_keywords):
         return {
            "valid": False,
            "message": "❌ Blocked: No valid approval route identified. Please mention 'ECAB' or a manager for approval."
        }

    return {
        "valid": True,
        "message": "✅ Validation Successful. Proceed to submit."
    }

def audit_emergency_changes(query):
    """
    Audits emergency changes based on a timeframe query.
    Returns an HTML table with the audit results.
    """
    import datetime
    
    # 1. Mock Data (Emergency Tickets)
    # In a real scenario, this would come from ServiceNow
    mock_tickets = [
        {
            "number": "CHG005001",
            "short_description": "Fix Critical Payment Gateway Failure",
            "justification": "Production down, customers cannot pay. Sev1 incident.",
            "risk": "High",
            "priority": "1 - Critical",
            "type": "Emergency",
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        },
        {
            "number": "CHG005002",
            "short_description": "Update Logo on Login Page",
            "justification": "Marketing wants the new logo up ASAP.",
            "risk": "Low",
            "priority": "4 - Low",
            "type": "Emergency",
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        },
        {
            "number": "CHG005003",
            "short_description": "Security Patch for Zero-Day Vulnerability",
            "justification": "Critical security patch required to prevent exploit.",
            "risk": "High",
            "priority": "1 - Critical",
            "type": "Emergency",
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        },
        {
            "number": "CHG005004",
            "short_description": "Restart Stuck Job Service",
            "justification": "Service stuck, impacting reporting.",
            "risk": "Moderate",
            "priority": "2 - High",
            "type": "Emergency",
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        },
        {
            "number": "CHG005005",
            "short_description": "Routine Server Reboot",
            "justification": "Forgot to do it in maintenance window.",
            "risk": "Low",
            "priority": "3 - Moderate",
            "type": "Emergency",
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        }
    ]
    
    # 2. Filter by Timeframe (Simple Logic)
    # If "last week" or "7 days", show all. If "yesterday", show only 1 day old.
    # For demo, we'll just show all if "audit" is requested, or filter slightly.
    
    filtered_tickets = mock_tickets
    timeframe_text = "Last 7 Days"
    
    if "yesterday" in query.lower():
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        filtered_tickets = [t for t in mock_tickets if t['created_at'] == yesterday]
        timeframe_text = "Yesterday"
        
    # 3. Audit Logic (The "Judge")
    audit_results = []
    
    for ticket in filtered_tickets:
        status = "Valid"
        reason = "Compliant with SOP."
        
        # Policy Check 1: Priority
        if ticket['priority'] in ["3 - Moderate", "4 - Low"]:
            status = "Invalid"
            reason = "Invalid: Priority is too low for Emergency change."
            
        # Policy Check 2: Justification Keywords
        valid_keywords = ["production down", "outage", "critical", "sev1", "security", "vulnerability", "exploit"]
        if not any(k in ticket['justification'].lower() for k in valid_keywords):
            status = "Invalid"
            reason = "Invalid: Justification does not indicate critical impact."
            
        # Policy Check 3: Routine work (heuristic)
        if "routine" in ticket['short_description'].lower() or "forgot" in ticket['justification'].lower():
            status = "Invalid"
            reason = "Invalid: Routine maintenance should not be an Emergency change."
            
        audit_results.append({
            "ticket": ticket,
            "status": status,
            "reason": reason
        })
        
    # 4. Generate HTML Output
    if not audit_results:
        return {"answer": f"No emergency changes found for {timeframe_text}."}
        
    html = f"""<div class="audit-container">
    <h3>🚨 Emergency Change Audit Report ({timeframe_text})</h3>
    <div class="table-responsive">
        <table class="audit-table">
            <thead>
                <tr>
                    <th>Ticket</th>
                    <th>Description</th>
                    <th>Status</th>
                    <th>Audit Reason</th>
                </tr>
            </thead>
            <tbody>"""
    
    for res in audit_results:
        status_class = "status-valid" if res['status'] == "Valid" else "status-invalid"
        icon = "✅" if res['status'] == "Valid" else "❌"
        
        html += f"""
                <tr>
                    <td><strong>{res['ticket']['number']}</strong></td>
                    <td>{res['ticket']['short_description']}</td>
                    <td><span class="status-badge {status_class}">{icon} {res['status']}</span></td>
                    <td>{res['reason']}</td>
                </tr>"""
        
    html += """
            </tbody>
        </table>
    </div>
    <div style="margin-top: 10px;">
        <button onclick="exportAuditTableToCSV()" class="export-btn">
            📥 Export to Excel
        </button>
    </div>
</div>
<style>
    .audit-container { margin: 10px 0; font-family: sans-serif; }
    .audit-container h3 { margin-bottom: 15px; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .table-responsive { overflow-x: auto; }
    .audit-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .audit-table th { background: #2c3e50; color: white; padding: 12px; text-align: left; font-weight: 600; }
    .audit-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
    .audit-table tr:hover { background: #f8f9fa; }
    .status-badge { padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; display: inline-block; }
    .status-valid { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .status-invalid { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .export-btn {
        background-color: #28a745;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        transition: background-color 0.2s;
    }
    .export-btn:hover {
        background-color: #218838;
    }
</style>"""
    
    return {"answer": html}
