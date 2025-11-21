import os
import csv
import datetime
import json
import requests
from requests.auth import HTTPBasicAuth
from collections import Counter, defaultdict
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
LOG_FILE = "query_logs.csv"
FEEDBACK_FILE = "feedback_logs.csv"

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret_key"

rag_chain = None

# --- Helper Functions: Logging ---
def log_interaction(question, answer):
    # Note: We removed the hardcoded 'unanswered_phrase' check because 
    # the bot might now say it in Spanish/German etc.
    # Simple logic: if answer is very short or contains "sorry/lo siento", maybe unanswered.
    status = "Answered" 
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Question", "Status"])
            writer.writerow([timestamp, question, status])
    except Exception as e:
        print(f"Logging error: {e}")

def log_feedback(feedback_type, message_content):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(FEEDBACK_FILE)
    try:
        with open(FEEDBACK_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Type", "Message_Snippet"])
            writer.writerow([timestamp, feedback_type, message_content[:100]])
    except Exception as e:
        print(f"Feedback logging error: {e}")

# --- FEATURE: ServiceNow Data Fetching (Kept in English as requested) ---
def get_servicenow_stats(group_by_field="state", chart_type="bar"):
    INSTANCE = os.environ.get("SERVICENOW_INSTANCE")
    USER = os.environ.get("SERVICENOW_USER")
    PASSWORD = os.environ.get("SERVICENOW_PASSWORD")

    if not all([INSTANCE, USER, PASSWORD]):
        mock_map = {
            "risk": {"labels": ["Very High", "High", "Moderate", "Low"], "data": [2, 5, 15, 30]},
            "priority": {"labels": ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"], "data": [1, 4, 20, 10]},
            "category": {"labels": ["Hardware", "Software", "Network", "Database"], "data": [12, 25, 8, 5]},
            "state": {"labels": ["New", "Assess", "Authorize", "Scheduled", "Closed"], "data": [10, 5, 8, 12, 40]}
        }
        selected_data = mock_map.get(group_by_field, mock_map["state"])
        
        return jsonify({
            "type": "chart",
            "text": f"Here is the breakdown of Change Requests by **{group_by_field.upper()}**:",
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
        })

    url = f"{INSTANCE}/api/now/stats/change_request"
    params = {
        "sysparm_count": "true",
        "sysparm_group_by": group_by_field,
        "sysparm_display_value": "true"
    }
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USER, PASSWORD), params=params)
        data = response.json()
        labels = []
        counts = []
        if 'result' in data:
            for group in data['result']:
                val = group['groupby_fields'][0]['value']
                count = int(group['stats']['count'])
                if count > 0:
                    labels.append(val if val else "Unknown")
                    counts.append(count)
        
        return jsonify({
            "type": "chart",
            "text": f"Found {sum(counts)} tickets grouped by **{group_by_field}**:",
            "chart_type": chart_type,
            "chart_data": {
                "labels": labels,
                "datasets": [{
                    "label": f"Changes by {group_by_field}",
                    "data": counts,
                    "backgroundColor": ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2'],
                    "borderWidth": 1
                }]
            }
        })
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"answer": "Error fetching data from ServiceNow."})

# --- Initialization ---
def initialize_rag_chain():
    global rag_chain
    try:
        print("Initializing RAG Chain...")
        loader = PyPDFDirectoryLoader("docs")
        documents = loader.load()
        if not documents:
            print("Warning: No PDF documents found in 'docs/' folder.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)
        print(f"Processed {len(docs)} document chunks.")

        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
        retriever = vectorstore.as_retriever()
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, convert_system_message_to_human=True)

        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # --- MULTI-LANGUAGE SYSTEM PROMPT ---
        qa_system_prompt = (
            "You are the 'Change Management Assistant', a professional AI chatbot. "
            "Your purpose is to answer questions about change management based on the provided context. "
            "Your knowledge base consists of multiple documents (SOPs, Policies, KB Articles).\n\n"
            
            "--- MULTI-LANGUAGE RULES (CRITICAL) ---\n"
            "1. **Detect Language:** Automatically detect the language of the user's question.\n"
            "2. **Respond in Kind:** You MUST answer in the EXACT SAME language as the user's question. (e.g., If user asks in Hindi, answer in Hindi).\n"
            "3. **Context Translation:** The provided context is in English. You must translate the relevant information from the context into the user's language to answer.\n\n"

            "--- BEHAVIORAL RULES ---\n"
            "1. **Greeting:** Respond naturally to greetings in the user's language.\n"
            "2. **Identity:** If asked who you are, introduce yourself as 'Change Management Assistant' (translated if needed).\n"
            "3. **Knowledge-Based Questions:** Answer based ONLY on the provided context below. Do not make up information.\n"
            "4. **No Context:** If the answer is not in the context, apologize and state you don't have information, BUT translate this refusal message into the user's language.\n"
            "5. **Formatting:** Use **Bold**, *Bullets*, and **Tables** for readability.\n"
            "6. **Source Citation:** At the end, mention the source document: *(Source: Document Name)*.\n"
            "7. **Conflict Handling:** If you find conflicting information, mention both.\n\n"

            "--- PROVIDED CONTEXT ---\n"
            "<context>\n{context}\n</context>"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        print("RAG Chain Ready!")

    except Exception as e:
        print(f"Error during initialization: {e}")

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html', role='User')

@app.route('/ask', methods=['POST'])
def ask_question():
    if not rag_chain:
        return jsonify({"error": "Chatbot not initialized."}), 500

    data = request.get_json()
    question = data.get('question')
    chat_history_json = data.get('chat_history', [])

    if not question:
        return jsonify({"error": "No question provided."}), 400

    # --- INTENT DETECTION (Charts - Keeps English) ---
    lower_q = question.lower()
    if any(x in lower_q for x in ["chart", "graph", "stats", "breakdown", "status"]):
        if "risk" in lower_q:
            return get_servicenow_stats(group_by_field="risk", chart_type="pie")
        elif "priority" in lower_q:
            return get_servicenow_stats(group_by_field="priority", chart_type="doughnut")
        elif "category" in lower_q:
            return get_servicenow_stats(group_by_field="category", chart_type="bar")
        else:
            return get_servicenow_stats(group_by_field="state", chart_type="bar")
    # ---------------------------------

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
        response = rag_chain.invoke({"input": question, "chat_history": chat_history})
        answer = response.get("answer", "Sorry, something went wrong.")
        log_interaction(question, answer)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"Processing Error: {e}")
        return jsonify({"error": "Failed to process question."}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    log_feedback(data.get('type'), data.get('content', ''))
    return jsonify({"status": "success"})

@app.route('/analytics')
def analytics():
    logs = []
    unanswered_list = []
    total_queries = 0
    all_questions = []
    daily_counts = defaultdict(int)

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                total_queries = len(rows)
                for row in rows:
                    logs.insert(0, row)
                    try:
                        date_key = datetime.datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                        daily_counts[date_key] += 1
                    except: pass
                    all_questions.append(row['Question'].strip())
                    if row['Status'] == 'Unanswered':
                        unanswered_list.append(row)
        except Exception as e:
            print(f"Error reading logs: {e}")

    sorted_dates = sorted(daily_counts.keys())
    chart_counts = [daily_counts[d] for d in sorted_dates]
    most_common_questions = Counter(all_questions).most_common(5)

    feedback_logs = []
    positive_fb = 0
    negative_fb = 0
    
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fb_rows = list(reader)[::-1]
                for row in fb_rows:
                    feedback_logs.append(row)
                    if row['Type'] == 'thumbs_up': positive_fb += 1
                    elif row['Type'] == 'thumbs_down': negative_fb += 1
        except Exception as e: pass

    return render_template('analytics.html', 
                           logs=logs[:50],
                           total=total_queries, 
                           unanswered_count=len(unanswered_list),
                           unanswered_list=unanswered_list,
                           most_common_questions=most_common_questions,
                           chart_labels=sorted_dates,
                           chart_data=chart_counts,
                           feedback_logs=feedback_logs,
                           positive_fb=positive_fb,
                           negative_fb=negative_fb)

if __name__ == '__main__':
    initialize_rag_chain()
    app.run(host='0.0.0.0', port=5000, debug=True)