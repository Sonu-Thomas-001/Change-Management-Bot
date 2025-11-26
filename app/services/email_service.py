from flask import jsonify
import urllib.parse
import re

def generate_email_draft(topic, full_query=""):
    # Combine topic and full query to check for keywords
    check_text = (full_query + " " + topic).lower()
    
    # Extract CR-ID (e.g., CR-123, CHG0001, or just numbers if context implies)
    cr_id_match = re.search(r'(cr-\d+|chg\d+|cr\d+)', check_text, re.IGNORECASE)
    cr_id = cr_id_match.group(0).upper() if cr_id_match else "[CR-ID]"
    
    # SOP Templates
    templates = {
        "acknowledgment": {
            "subject": f"Change Request {cr_id} Acknowledgment",
            "body": (
                "Dear [Requester Name],\n\n"
                f"Your Change Request {cr_id} has been received and is under review. "
                "The assigned Change Manager is [Manager Name], and the expected review timeline is [Timeline]. "
                "Please ensure all supporting documentation is uploaded.\n\n"
                "Regards,\n"
                "Change Management Team, ABC Bank"
            )
        },
        "status": {
            "subject": f"Status Update for Change Request {cr_id}",
            "body": (
                "Dear [Stakeholder Name],\n\n"
                f"The status of Change Request {cr_id} is currently [Stage]. "
                "The next action is scheduled for [Date/Time]. "
                "Please review pending tasks and contact [Manager Name] at [Email] for further details.\n\n"
                "Regards,\n"
                "Change Management Office, ABC Bank"
            )
        },
        "exception": {
            "subject": f"Exception Approval Request for {cr_id}",
            "body": (
                "Dear [Approver Name],\n\n"
                f"We request approval for an exception to standard change procedures for Change Request {cr_id}. "
                "The reason is [Urgency/Incident Summary]. "
                "The associated risks and mitigation plans are attached for your review.\n\n"
                "Please provide approval at the earliest to proceed.\n\n"
                "Regards,\n"
                "Change Management Team, ABC Bank"
            )
        }
    }

    # Determine which template to use
    selected_template = None
    if "acknowledg" in check_text or "receipt" in check_text:
        selected_template = templates["acknowledgment"]
    elif "status" in check_text or "update" in check_text:
        selected_template = templates["status"]
    elif "exception" in check_text or "approval" in check_text:
        selected_template = templates["exception"]
    
    if selected_template:
        subject = selected_template["subject"]
        body = selected_template["body"]
    else:
        # Fallback to generic template
        subject = f"Important Update: {topic}"
        body = (
            f"Hello Team,\n\n"
            f"This is an announcement regarding {topic}.\n\n"
            f"Please be advised that...\n\n"
            f"Best regards,\n"
            f"[Your Name]"
        )
    
    # URL Encode for Mailto Link
    subject_enc = urllib.parse.quote(subject)
    body_enc = urllib.parse.quote(body)
    
    mailto_link = f"mailto:?subject={subject_enc}&body={body_enc}"
    
    button_html = (
        f"<a href='{mailto_link}' "
        f"style='background-color: #007bff; color: white; padding: 8px 16px; "
        f"text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; margin-bottom: 10px;'>"
        f"📧 Draft in Outlook"
        f"</a>"
    )
    
    email_preview = (
        f"<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; font-family: monospace; white-space: pre-wrap; color: #333;'>"
        f"<strong>Subject:</strong> {subject}\n\n"
        f"{body}"
        f"</div>"
    )
    
    return jsonify({
        "answer": f"Here is a draft for your email regarding **{topic}**:<br><br>{button_html}{email_preview}",
        "disable_copy": True
    })
