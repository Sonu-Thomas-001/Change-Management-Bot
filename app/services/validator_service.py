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
