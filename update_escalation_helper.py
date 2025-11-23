import csv
import os

# Script to update log_escalation function behavior
# This will be manually integrated into app.py

def log_escalation_new(chat_history, reason="User Request"):
    """
    Updated version of log_escalation that extracts user query and bot response
    """
    import datetime
    
    ESCALATION_FILE = "escalation_logs.csv"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(ESCALATION_FILE)
    
    try:
        with open(ESCALATION_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Reason", "User_Query", "Bot_Response"])
            
            # Extract last user query and bot response from chat history
            user_query = "N/A"
            bot_response = "N/A"
            
            if chat_history and isinstance(chat_history, list):
                # Find the last human message and AI message
                for msg in reversed(chat_history):
                    if isinstance(msg, dict):
                        if msg.get('type') == 'human' and user_query == "N/A":
                            user_query = msg.get('content', 'N/A')[:200]  # Limit to 200 chars
                        elif msg.get('type') == 'ai' and bot_response == "N/A":
                            bot_response = msg.get('content', 'N/A')[:200]  # Limit to 200 chars
                    
                    # Stop once we have both
                    if user_query != "N/A" and bot_response != "N/A":
                        break
            
            writer.writerow([timestamp, reason, user_query, bot_response])
            print(f"*** ESCALATION ALERT ***\nReason: {reason}\nTimestamp: {timestamp}\nSee {ESCALATION_FILE} for details.\n************************")
    except Exception as e:
        print(f"Escalation logging error: {e}")

# Instructions:
# Replace the log_escalation function in app.py (lines 62-76) with the log_escalation_new function above
# Then rename log_escalation_new to log_escalation
