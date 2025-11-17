import os
import csv
import datetime
from collections import Counter
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

        # --- LOCKED PROMPT WITH GREETING HANDLING ---
        qa_system_prompt = (
            "You are the 'Change Management Assistant', a friendly and professional AI chatbot. "
            "Your primary purpose is to answer employee questions about the change management process based on the provided context. "
            "Be conversational and helpful.\n\n"
            
            "--- BEHAVIORAL RULES ---\n"
            "1.  **Greeting:** If the user says 'hi', 'hello', or a similar greeting, respond with a friendly greeting (e.g., 'Hello! How can I help you with change management today?') and do NOT check the context.\n"
            "2.  **Identity:** If the user asks who you are, introduce yourself as the 'Change Management Assistant'.\n"
            "3.  **Knowledge-Based Questions:** For all other questions, answer based ONLY on the provided context below. Do not make up information.\n"
            "4.  **No Context:** If the answer is not in the context, say exactly: 'I'm sorry, I don't have information on that topic in my current knowledge base.'\n"
            "5.  **Formatting:** Use clear bullet points and bold text for readability.\n\n"

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
    # 1. Parse Query Logs
    logs = []
    unanswered_count = 0
    all_text = ""
    total_queries = 0
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)[::-1] 
                total_queries = len(rows)
                for row in rows:
                    logs.append(row)
                    if row['Status'] == 'Unanswered':
                        unanswered_count += 1
                    all_text += " " + row['Question'].lower()
        except Exception as e:
            print(f"Error reading query logs: {e}")

    # 2. Parse Feedback Logs
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

    # 3. Keywords
    stop_words = {'what', 'is', 'the', 'how', 'to', 'a', 'an', 'of', 'in', 'for', 'template', 'change', 'does', 'can', 'i', 'give', 'me'}
    words = [w for w in all_text.split() if w not in stop_words and len(w) > 3]
    most_common_words = Counter(words).most_common(8)

    return render_template('analytics.html', 
                           logs=logs, 
                           total=total_queries, 
                           unanswered=unanswered_count,
                           topics=most_common_words,
                           feedback_logs=feedback_logs,
                           positive_fb=positive_fb,
                           negative_fb=negative_fb)

if __name__ == '__main__':
    initialize_rag_chain()
    app.run(host='0.0.0.0', port=5000, debug=True)