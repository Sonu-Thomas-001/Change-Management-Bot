import os
import csv
import datetime
from app.config import Config

def log_interaction(question, answer):
    # Define triggers for unanswered queries
    low_confidence_triggers = [
        "i don't know", "i'm not sure", "no information found", 
        "apologies", "sorry", "cannot answer", "do not have information",
        "i don't have", "i do not have", "unable to", "not able to",
        "can't answer", "cannot provide", "not available", "no data",
        "i'm unable", "i am unable", "don't have enough", "insufficient information"
    ]
    
    # Default status
    status = "Answered"
    
    # Check if answer contains any low confidence triggers
    print(f"DEBUG: Logging Interaction - Answer: {answer[:50]}...")
    if any(trigger in answer.lower() for trigger in low_confidence_triggers):
        status = "Unanswered"
        print(f"DEBUG: Status set to Unanswered (Trigger match)")
    else:
        print(f"DEBUG: Status set to Answered (No trigger match)")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(Config.LOG_FILE)
    try:
        # Ensure file ends with newline before appending
        if file_exists:
            with open(Config.LOG_FILE, mode='rb+') as f:
                f.seek(0, 2) # Go to end
                if f.tell() > 0:
                    f.seek(-1, 1)
                    if f.read(1) != b'\n':
                        f.write(b'\n')

        with open(Config.LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Question", "Status"])
            writer.writerow([timestamp, question, status])
    except Exception as e:
        print(f"Logging error: {e}")

def log_feedback(feedback_type, message_content):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(Config.FEEDBACK_FILE)
    try:
        with open(Config.FEEDBACK_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Type", "Message_Snippet"])
            writer.writerow([timestamp, feedback_type, message_content[:100]])
    except Exception as e:
        print(f"Feedback logging error: {e}")

def log_escalation(chat_history, reason="User Request"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(Config.ESCALATION_FILE)
    try:
        with open(Config.ESCALATION_FILE, mode='a', newline='', encoding='utf-8') as file:
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
            print(f"*** ESCALATION ALERT ***\nReason: {reason}\nTimestamp: {timestamp}\nSee {Config.ESCALATION_FILE} for details.\n************************")
    except Exception as e:
        print(f"Escalation logging error: {e}")
