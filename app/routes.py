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

    # --- FEATURE: Emergency Change Validator & Auditor ---
    if "emergency" in lower_q:
        # Auditor Intent
        if any(keyword in lower_q for keyword in ["audit", "analyze", "invalid", "report", "review"]):
            from app.services.validator_service import audit_emergency_changes
            return jsonify(audit_emergency_changes(question))
            
        # Validator Intent
        if any(keyword in lower_q for keyword in ["change", "create", "raise", "draft"]):
            validation_result = validate_emergency_change(question)
            return jsonify({"answer": validation_result["message"]})

    # --- FEATURE: Smart Change Creator ---
    from app.services.smart_change_creator import process_smart_change_intent
    smart_response = process_smart_change_intent(question)
    if smart_response:
        return smart_response
    
    # 1. Ticket Status Lookup
    
    # 1. Ticket Status Lookup
    ticket_match = re.search(r"\b(cr|chg|mock)[-]?(\d+)\b", lower_q)
    
    if ticket_match and ("status" in lower_q or "check" in lower_q or "ticket" in lower_q):
        full_match = ticket_match.group(0).upper()
        return get_ticket_details(full_match)
            
    # 2. Create Ticket Intent
    if "create" in lower_q and ("change request" in lower_q or "ticket" in lower_q):
        return create_change_request(
            description=question,
            impact="Low",
            risk="Low"
        )

    # 3. Pending Approvals Intent
    if any(keyword in lower_q for keyword in ["pending approval", "my approval", "approvals", "need to approve", "approval request"]):
        return get_pending_approvals()

    # 4. Pending Tasks Intent
    if any(keyword in lower_q for keyword in ["pending task", "my task", "tasks", "assigned to me", "task list"]):
        return get_pending_tasks()

    # 5. Draft Email Intent
    if "draft" in lower_q and ("email" in lower_q or "communication" in lower_q or "template" in lower_q):
        topic = "Change Request"
        if "for" in lower_q:
            topic = question.split("for", 1)[1].strip()
        elif "about" in lower_q:
            topic = question.split("about", 1)[1].strip()
        return generate_email_draft(topic, question)

    # 6. Risk Scoring Intent
    if "risk" in lower_q and ("score" in lower_q or "analyze" in lower_q or "evaluate" in lower_q or "assess" in lower_q):
        return analyze_risk_score(question)

    # 7. Schedule Conflict Detection Intent
    if any(keyword in lower_q for keyword in ["schedule", "plan for", "implement on", "can i", "available"]):
        # Check if there's a date reference
        has_date = re.search(r'\d{4}-\d{1,2}-\d{1,2}', question) or \
                   re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', question, re.IGNORECASE) or \
                   any(word in lower_q for word in ["weekend", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
        
        if has_date:
            return check_schedule_conflict(question)

    # 8. Scheduled Changes Query Intent
    scheduled_keywords = ["planned", "scheduled", "upcoming", "completed", "closed"]
    time_keywords = ["today", "tomorrow", "weekend", "week", "month", "changes"]
    
    if any(x in lower_q for x in scheduled_keywords) or \
       ("change" in lower_q and any(x in lower_q for x in time_keywords)):
        # Check if it's asking for scheduled changes
        if "change" in lower_q or "changes" in lower_q:
            return get_scheduled_changes(question)

    # 9. Enhanced Chart/Stats Intent  
    chart_keywords = ["chart", "graph", "stats", "breakdown", "metrics", "trend", "workload", "how many", "show", "display", "visualize"]
    if any(x in lower_q for x in chart_keywords):
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
            # Check if asking for comparison or counts
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
                       
    # Fallback for "status" if it didn't match a specific ticket
    if "status" in lower_q and not ticket_match:
         return get_servicenow_stats(group_by_field="state", chart_type="bar")

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
