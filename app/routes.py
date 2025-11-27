import os
import re
import csv
import datetime
from collections import Counter, defaultdict
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from langchain_core.messages import HumanMessage, AIMessage

from app.config import Config
from app.utils import check_schedule_conflict
from app.services.logging_service import log_interaction, log_feedback, log_escalation
from app.services.data_service import (
    get_servicenow_stats, create_change_request,
    get_pending_approvals, get_pending_tasks
)
from app.services.ticket_service import get_ticket_details
from app.services.email_service import generate_email_draft
from app.services.rag_service import analyze_risk_score
import app.services.rag_service as rag_service
from app.services.scheduled_changes_service import get_scheduled_changes, export_scheduled_changes
from app.services.validator_service import validate_emergency_change

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'User':
            if username == 'user' and password == 'password':
                session['user'] = username
                session['role'] = role
                return redirect(url_for('main.index'))
            else:
                flash('Invalid User credentials')
        elif role == 'Change Admin':
            if username == 'admin' and password == 'admin':
                session['user'] = username
                session['role'] = role
                return redirect(url_for('main.analytics'))
            else:
                flash('Invalid Admin credentials')
        else:
            flash('Invalid Role selected')
            
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    return render_template('index.html', role=session.get('role'))

@main_bp.route('/ask', methods=['POST'])
def ask_question():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not rag_service.rag_chain:
        return jsonify({"error": "Chatbot not initialized."}), 500

    data = request.get_json()
    question = data.get('question')
    chat_history_json = data.get('chat_history', [])

    if not question:
        return jsonify({"error": "No question provided."}), 400

    lower_q = question.lower()

    # --- LLM-BASED ROUTING ---
    intent = rag_service.classify_intent(question)
    print(f"DEBUG: Detected Intent: {intent}")

    # 1. Ticket Status Lookup
    if intent == "TICKET_STATUS":
        ticket_match = re.search(r"\b(cr|chg|mock)[-]?(\d+)\b", lower_q)
        if ticket_match:
            full_match = ticket_match.group(0).upper()
            return get_ticket_details(full_match)
        else:
            # Fallback if no ticket number found, let RAG handle it or ask for number
            pass 

    # 2. Create Ticket Intent
    if intent == "CREATE_CHANGE":
        # Check if this is a confirmation to clone
        clone_match = re.search(r"clone\s+(CR|CHG|MOCK)[-]?(\d+)", lower_q)
        if clone_match:
            # Parse details for cloning
            ticket_number = clone_match.group(0).split()[1].upper()
            
            # Extract dates if present (simple extraction)
            start_date = "2025-12-01 09:00:00" # Default/Mock
            end_date = "2025-12-02 17:00:00"   # Default/Mock
            
            # Try to find dates in input
            date_matches = re.findall(r"\d{4}-\d{2}-\d{2}", question)
            if len(date_matches) >= 2:
                start_date = f"{date_matches[0]} 09:00:00"
                end_date = f"{date_matches[1]} 17:00:00"
            
            # Extract Assignee if present
            assigned_to = "Unassigned"
            assignee_match = re.search(r"assigned to\s+([a-zA-Z\s]+)", lower_q)
            if assignee_match:
                assigned_to = assignee_match.group(1).strip().title()

            # Fetch template details
            from app.services.smart_change_creator import get_change_details, create_change_request as smart_create
            
            template_ticket = get_change_details(ticket_number)
            
            if not template_ticket:
                 return jsonify({"answer": f"❌ I could not find the template ticket **{ticket_number}**. Please check the number and try again."})
            
            new_ticket = smart_create(template_ticket, start_date, end_date, assigned_to)
            
            if new_ticket:
                 return jsonify({"answer": f"✅ **Smart Clone Successful!**\n\nI have created a new Change Request **{new_ticket}** based on {ticket_number}.\n\n*   **Scheduled**: {start_date} to {end_date}\n*   **Assigned To**: {assigned_to}\n*   **Status**: Draft"})
            else:
                 return jsonify({"answer": "❌ Failed to create cloned ticket."})

        # Otherwise, search for suggestions
        from app.services.smart_change_creator import find_similar_changes
        suggestion = find_similar_changes(question)
        
        if suggestion:
            return jsonify({"answer": f"💡 **Smart Suggestion**: I found a successful past change that matches your request:\n\n**{suggestion['number']}**: {suggestion['short_description']}\n\nWould you like to use this as a template? If so, reply with:\n`Clone {suggestion['number']} for YYYY-MM-DD to YYYY-MM-DD assigned to [Name]`"})
            
        # Fallback to standard creation if no smart match
        return create_change_request(
            description=question,
            impact="Low",
            risk="Low"
        )

    # 3. Pending Approvals Intent
    if intent == "PENDING_APPROVALS":
        return get_pending_approvals()

    # 4. Pending Tasks Intent
    if intent == "PENDING_TASKS":
        return get_pending_tasks()

    # 5. Draft Email Intent
    if intent == "DRAFT_EMAIL":
        topic = "Change Request"
        if "for" in lower_q:
            topic = question.split("for", 1)[1].strip()
        elif "about" in lower_q:
            topic = question.split("about", 1)[1].strip()
        return generate_email_draft(topic, question)

    # 6. Risk Scoring Intent
    if intent == "RISK_ANALYSIS":
        return analyze_risk_score(question)

    # 7. Schedule Conflict & Scheduled Changes Intent
    if intent == "SCHEDULE_QUERY":
        # Check for conflict detection first (specific type of schedule query)
        if any(keyword in lower_q for keyword in ["conflict", "available", "can i"]):
             return check_schedule_conflict(question)
        return get_scheduled_changes(question)

    # 8. Enhanced Chart/Stats Intent  
    if intent == "SHOW_STATS":
        if "risk" in lower_q:
            return get_servicenow_stats(group_by_field="risk", chart_type="pie")
        elif "priority" in lower_q:
            return get_servicenow_stats(group_by_field="priority", chart_type="doughnut")
        elif "category" in lower_q:
            return get_servicenow_stats(group_by_field="category", chart_type="bar")
        elif "assignee" in lower_q or "who" in lower_q:
            return get_servicenow_stats(group_by_field="assignee", chart_type="bar")
        elif "type" in lower_q and "change" in lower_q:
            return get_servicenow_stats(group_by_field="change_type", chart_type="pie")
        elif any(word in lower_q for word in ["approval", "approved", "rejected", "reject", "accept", "accepted", "deny", "denied"]):
            if any(word in lower_q for word in ["vs", "versus", "compared", "comparison"]):
                return get_servicenow_stats(group_by_field="approval_rate", chart_type="pie")
            return get_servicenow_stats(group_by_field="approval_rate", chart_type="doughnut")
        elif "month" in lower_q or "trend" in lower_q:
            return get_servicenow_stats(group_by_field="monthly_trend", chart_type="line")
        elif "completion" in lower_q or "duration" in lower_q:
            return get_servicenow_stats(group_by_field="completion_time", chart_type="bar")
        elif "impact" in lower_q:
            return get_servicenow_stats(group_by_field="impact", chart_type="pie")
        elif "team" in lower_q or "group" in lower_q or "workload" in lower_q:
            return get_servicenow_stats(group_by_field="assignment_group", chart_type="bar")
        else:
            return get_servicenow_stats(group_by_field="state", chart_type="bar")
            
    # 9. Emergency Change Validator & Auditor
    if intent == "AUDIT_EMERGENCY":
        from app.services.validator_service import audit_emergency_changes
        return jsonify(audit_emergency_changes(question))
        
    if intent == "VALIDATE_EMERGENCY":
        validation_result = validate_emergency_change(question)
        return jsonify({"answer": validation_result["message"]})

    chat_history = []
    for msg in chat_history_json:
        if msg.get('type') == 'human':
            chat_history.append(HumanMessage(content=msg.get('content')))
        elif msg.get('type') == 'ai':
            chat_history.append(AIMessage(content=msg.get('content')))
        elif msg.get('type') == 'chart':
            chart_text = msg.get('content', {}).get('text', 'Visual Chart Displayed')
            chat_history.append(AIMessage(content=f"[{chart_text}]"))

    try:
        # Pass user role to the RAG service for personality adaptation
        user_role = session.get('role', 'User')
        
        response = rag_service.answer_question(question, chat_history, user_role)
        answer = response.get("answer", "Sorry, something went wrong.")
        log_interaction(question, answer)
        
        # Simple heuristic for low confidence
        low_confidence = False
        low_confidence_triggers = [
            "i don't know", "i'm not sure", "no information found", 
            "apologies", "sorry", "cannot answer",
            "i don't have", "i do not have", "unable to", "not able to",
            "can't answer", "cannot provide", "not available", "no data",
            "i'm unable", "i am unable", "don't have enough", "insufficient information"
        ]
        if any(trigger in answer.lower() for trigger in low_confidence_triggers):
            low_confidence = True

        return jsonify({"answer": answer, "low_confidence": low_confidence})
    except Exception as e:
        print(f"Processing Error: {e}")
        return jsonify({"error": "Failed to process question."}), 500

@main_bp.route('/feedback', methods=['POST'])
def feedback():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    log_feedback(data.get('type'), data.get('content', ''))
    return jsonify({"status": "success"})

@main_bp.route('/escalate', methods=['POST'])
def escalate():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    chat_history = data.get('chat_history', [])
    reason = data.get('reason', 'User Request')
    
    log_escalation(chat_history, reason)
    
    return jsonify({"status": "success", "message": "Request sent to Change Manager."})

@main_bp.route('/analytics')
def analytics():
    if 'user' not in session or session.get('role') != 'Change Admin':
        return redirect(url_for('main.login'))
        
    logs = []
    unanswered_list = []
    all_questions = []
    daily_volume = defaultdict(int)
    hourly_volume = defaultdict(int)
    status_counts = {"Answered": 0, "Unanswered": 0}
    
    total_queries = 0
    
    if os.path.exists(Config.LOG_FILE):
        try:
            with open(Config.LOG_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                total_queries = len(rows)
                
                for row in rows:
                    logs.insert(0, row)
                    
                    try:
                        dt = datetime.datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S")
                        date_key = dt.strftime("%Y-%m-%d")
                        hour_key = dt.strftime("%H:00")
                        
                        daily_volume[date_key] += 1
                        hourly_volume[hour_key] += 1
                    except: pass

                    all_questions.append(row['Question'].strip())

                    stat = row['Status']
                    if stat in status_counts:
                        status_counts[stat] += 1
                    
                    if stat == 'Unanswered':
                        unanswered_list.append(row)

        except Exception as e:
            print(f"Log Error: {e}")

    feedback_data = {"thumbs_up": 0, "thumbs_down": 0}
    recent_feedback = []
    
    if os.path.exists(Config.FEEDBACK_FILE):
        try:
            with open(Config.FEEDBACK_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fb_rows = list(reader)
                for row in fb_rows:
                    recent_feedback.insert(0, row)
                    if row['Type'] in feedback_data:
                        feedback_data[row['Type']] += 1
        except Exception as e: pass

    escalations = []
    if os.path.exists(Config.ESCALATION_FILE):
        try:
            with open(Config.ESCALATION_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                escalations = list(reader)
                escalations.reverse() # Newest first
        except Exception as e: pass

    success_rate = 0
    if total_queries > 0:
        success_rate = round((status_counts["Answered"] / total_queries) * 100, 1)

    total_feedback = feedback_data["thumbs_up"] + feedback_data["thumbs_down"]
    satisfaction_score = 0
    if total_feedback > 0:
        satisfaction_score = round((feedback_data["thumbs_up"] / total_feedback) * 100, 1)

    # Fill in missing dates for a continuous timeline
    if daily_volume:
        min_date_str = min(daily_volume.keys())
        max_date_str = max(daily_volume.keys())
        
        current_date = datetime.datetime.strptime(min_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(max_date_str, "%Y-%m-%d")
        
        sorted_dates = []
        volume_data = []
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            sorted_dates.append(date_str)
            volume_data.append(daily_volume.get(date_str, 0))
            current_date += datetime.timedelta(days=1)
    else:
        sorted_dates = []
        volume_data = []

    stop_words = {'what', 'is', 'the', 'how', 'to', 'a', 'an', 'of', 'in', 'for', 'template', 'change', 'does', 'can', 'i', 'give', 'me', 'show'}
    words = [w for w in " ".join(all_questions).lower().split() if w not in stop_words and len(w) > 3]
    top_keywords = Counter(words).most_common(8)

    return render_template('analytics.html', 
                           total=total_queries, 
                           success_rate=success_rate,
                           satisfaction_score=satisfaction_score,
                           unanswered_count=len(unanswered_list),
                           chart_labels=sorted_dates,
                           chart_data=volume_data,
                           status_counts=[status_counts["Answered"], status_counts["Unanswered"]],
                           feedback_counts=[feedback_data["thumbs_up"], feedback_data["thumbs_down"]],
                           logs=logs[:50], 
                           unanswered_list=unanswered_list,
                           top_keywords=top_keywords,
                           recent_feedback=recent_feedback[:10],
                           escalations=escalations)

@main_bp.route('/export_changes')
def export_changes():
    """
    Export scheduled changes to CSV.
    """
    if 'user' not in session:
        return redirect(url_for('main.login'))
        
    query = request.args.get('query', '')
    if not query:
        return "No query provided", 400
        
    return export_scheduled_changes(query)
