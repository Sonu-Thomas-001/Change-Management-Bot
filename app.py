import os
from flask import Flask, request, jsonify, render_template
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- 1. Initialize Flask App ---
app = Flask(__name__)

# --- 2. Configure RAG Chain (runs once on startup) ---
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file or environment.")

# Global variable to hold the final RAG chain
rag_chain = None

def initialize_rag_chain():
    """
    Initializes the full conversational RAG chain.
    """
    global rag_chain

    try:
        print("Initializing Conversational RAG Chain...")

        # Load documents
        loader = PyPDFDirectoryLoader("docs")
        documents = loader.load()
        if not documents:
            print("Warning: No documents found in the 'docs' directory.")
            return

        # Split documents (using a smaller chunk size for better specificity)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)
        print(f"Loaded and split {len(docs)} document chunks.")

        # Create embeddings and vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
        retriever = vectorstore.as_retriever()

        # Define the LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

        # Contextualizer Prompt for rephrasing a follow-up question
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        # Create a history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # --- THIS IS THE UPDATED PROMPT ---
        # Main prompt for answering the question based on retrieved context
        qa_system_prompt = (
            "You are the 'Change Management Assistant,' a friendly and professional AI chatbot for ABC Bank. "
            "Your primary purpose is to answer employee questions about the company's change management process based on a provided knowledge base. "
            "Be conversational and helpful.\n\n"
            
            "--- BEHAVIORAL RULES ---\n"
            "1.  **Greeting:** If the user says 'hi', 'hello', or a similar greeting, respond with a friendly greeting and ask how you can help.\n"
            "2.  **Identity:** If the user asks who you are (e.g., 'who are you?', 'what are you?'), introduce yourself as the 'Change Management Assistant' and explain your purpose.\n"
            "3.  **Knowledge-Based Questions:** For any other question related to change management, you MUST answer based ONLY on the provided context below. Do not make up information.\n"
            "4.  **No Context:** If you cannot find the answer in the context for a knowledge-based question, respond with 'I'm sorry, I don't have information on that topic in my current knowledge base.'\n"
            "5.  **Formatting:** When providing details for a specific template, format the information as a clean, bulleted list with bold labels (e.g., - **Template Name:** [Name]).\n\n"

            "--- PROVIDED CONTEXT ---\n"
            "<context>\n{context}\n</context>"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Chain for generating an answer from the question and context
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        # Final RAG chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        print("Conversational RAG Chain Initialized Successfully!")

    except Exception as e:
        print(f"Error initializing RAG chain: {e}")

# --- 3. Define Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handles incoming questions and chat history from the frontend."""
    if not rag_chain:
        return jsonify({"error": "Chatbot is not initialized. Check server logs."}), 500

    data = request.get_json()
    question = data.get('question')
    chat_history_json = data.get('chat_history', [])

    if not question:
        return jsonify({"error": "No question provided."}), 400

    # Convert JSON history to LangChain message objects
    chat_history = []
    for msg in chat_history_json:
        if msg.get('type') == 'human':
            chat_history.append(HumanMessage(content=msg.get('content')))
        elif msg.get('type') == 'ai':
            chat_history.append(AIMessage(content=msg.get('content')))

    try:
        # Invoke the chain with the question and history
        response = rag_chain.invoke({"input": question, "chat_history": chat_history})
        answer = response.get("answer", "Sorry, something went wrong.")
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"Error during chain invocation: {e}")
        return jsonify({"error": "Failed to process the question."}), 500

# --- 4. Run the Application ---
if __name__ == '__main__':
    initialize_rag_chain()
    app.run(host='0.0.0.0', port=5000, debug=True)