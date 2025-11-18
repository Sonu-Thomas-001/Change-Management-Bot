import os
import csv
import datetime
from collections import Counter, defaultdict
from flask import Flask, request, jsonify, render_template
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
# Use /tmp/ for cloud compatibility, or just "query_logs.csv" for local
LOG_FILE = "query_logs.csv" 
FEEDBACK_FILE = "feedback_logs.csv"

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

app = Flask(__name__)

rag_chain = None

# --- Helper Functions ---
def log_interaction(question, answer):
    unanswered_phrase = "I'm sorry, I don't have information"
    status = "Unanswered" if unanswered_phrase in answer else "Answered"
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
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

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

        # --- UPDATED PROMPT (Preserves Styling + Adds Source Citation) ---
        qa_system_prompt = (
            "You are the 'Change Management Assistant', a friendly and professional AI chatbot. "
            "Your primary purpose is to answer employee questions about the change management process based on the provided context. "
            "Your knowledge base consists of multiple documents (SOPs, Policies, KB Articles). "
            "Be conversational and helpful.\n\n"
            
            "--- BEHAVIORAL RULES ---\n"
            "1.  **Greeting:** If the user says 'hi', 'hello', or a similar greeting, respond with a friendly greeting (e.g., 'Hello! How can I help you with change management today?') and do NOT check the context.\n"
            "2.  **Identity:** If the user asks who you are, introduce yourself as the 'Change Management Assistant'.\n"
            "3.  **Knowledge-Based Questions:** For all other questions, answer based ONLY on the provided context below. Do not make up information.\n"
            "4.  **No Context:** If the answer is not in the context, say exactly: 'I'm sorry, I don't have information on that topic in my current knowledge base.'\n"
            "5.  **Formatting:** You must format your answers to be highly readable using Markdown:\n"
            "    - Use **Headings** (###) to separate sections.\n"
            "    - Use **Bold text** for key terms and important concepts.\n"
            "    - Use **Bullet points** for lists and steps.\n"
            "    - Use **Tables** when comparing data (like templates, roles, or timelines).\n"
            "6.  **Source Citation:** At the end of your answer, you MUST mention which document you got the information from. Use the format: *(Source: Document Name)*.\n"
            "7.  **Conflict Handling:** If you find conflicting information between documents, mention both and ask the user for clarification.\n\n"

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
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    if not rag_chain:
        return jsonify({"error": "Chatbot not initialized."}), 500

    data = request.get_json()
    question = data.get('question')
    # History is now managed by Frontend mostly, but backend expects it
    chat_history_json = data.get('chat_history', [])
    
    if not question:
        return jsonify({"error": "No question provided."}), 400

    chat_history = []
    for msg in chat_history_json:
        if msg.get('type') == 'human':
            chat_history.append(HumanMessage(content=msg.get('content')))
        elif msg.get('type') == 'ai':
            chat_history.append(AIMessage(content=msg.get('content')))

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
    fb_type = data.get('type')
    content = data.get('content', '')
    log_feedback(fb_type, content)
    return jsonify({"status": "success"})

@app.route('/analytics')
def analytics():
    logs = []
    unanswered_list = []
    total_queries = 0
    all_questions = []
    daily_counts = defaultdict(int)

    # 1. Process Query Logs
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                total_queries = len(rows)
                for row in rows:
                    # For Main Table (Reverse Order)
                    logs.insert(0, row)
                    
                    # For Daily Trend Chart
                    try:
                        date_key = datetime.datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                        daily_counts[date_key] += 1
                    except:
                        pass

                    all_questions.append(row['Question'].strip())

                    if row['Status'] == 'Unanswered':
                        unanswered_list.append(row)

        except Exception as e:
            print(f"Error reading query logs: {e}")

    # 2. Sort Date Data
    sorted_dates = sorted(daily_counts.keys())
    chart_counts = [daily_counts[d] for d in sorted_dates]

    # 3. Most Asked
    most_common_questions = Counter(all_questions).most_common(5)

    # 4. Process Feedback
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
                    if row['Type'] == 'thumbs_up':
                        positive_fb += 1
                    elif row['Type'] == 'thumbs_down':
                        negative_fb += 1
        except Exception as e:
            print(f"Error reading feedback logs: {e}")

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