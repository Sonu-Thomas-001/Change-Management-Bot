# Script to update the log_escalation function in app.py
import re

# Read the current app.py file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the old function
old_function = '''def log_escalation(chat_history, reason="User Request"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(ESCALATION_FILE)
    try:
        with open(ESCALATION_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Reason", "Chat_Snippet"])
            
            # Summarize chat history for the log
            snippet = str(chat_history)[-500:] if chat_history else "No history"
            writer.writerow([timestamp, reason, snippet])
            print(f"*** ESCALATION ALERT ***\\nReason: {reason}\\nTimestamp: {timestamp}\\nSee {ESCALATION_FILE} for details.\\n************************")
    except Exception as e:
        print(f"Escalation logging error: {e}")'''

# Define the new function
new_function = '''def log_escalation(chat_history, reason="User Request"):
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
            print(f"*** ESCALATION ALERT ***\\nReason: {reason}\\nTimestamp: {timestamp}\\nSee {ESCALATION_FILE} for details.\\n************************")
    except Exception as e:
        print(f"Escalation logging error: {e}")'''

# Replace the function
content = content.replace(old_function, new_function)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully updated log_escalation function in app.py")
