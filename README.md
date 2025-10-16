Change Management Assistant Chatbot 🤖
This project is a fully functional, conversational AI chatbot designed to answer questions about a company's change management process. It uses a Retrieval-Augmented Generation (RAG) architecture with Google's Gemini Pro to provide accurate answers based on a custom knowledge base of PDF documents.

The user interface is a clean, modern web-based chat window built with Flask, HTML, CSS, and JavaScript.

✨ Features
Conversational Memory: The chatbot can understand the context of a conversation and answer follow-up questions.

Knowledge Base Integration: Easily add your own PDF documents (SOPs, FAQs, etc.) to the docs/ folder to create a custom knowledge base.

Accurate, Sourced Answers: Built on a RAG architecture to prevent the AI from making up information and ensure answers are based only on the provided documents.

Markdown Rendering: The UI correctly formats the AI's responses, displaying lists, bold text, and tables for better readability.

Friendly Personality: The chatbot is programmed to handle greetings and questions about itself in a friendly, conversational manner.

Easy to Deploy: A simple, self-contained web application using Python and Flask.

🛠️ Tech Stack
Backend: Python, Flask

AI & Machine Learning: LangChain, Google Gemini Pro (gemini-1.5-flash), ChromaDB (for vector storage)

Frontend: HTML, CSS, JavaScript

UI Formatting: marked.js

📂 Project Structure
The project uses a simple and organized folder structure:

/change-management-chatbot
│
├── app.py              # Main Python/Flask application
├── README.md           # This file
├── .env                # For storing your API key
│
├── templates/
│   └── index.html      # Frontend user interface
│
├── static/
│   ├── style.css       # Styling for your UI
│   └── script.js       # JavaScript for interactivity
│
└── docs/
    └── (Your SOP and other PDF files go here)
🚀 Setup and Installation
Follow these steps to get the chatbot running on your local machine.

1. Clone the Repository
First, clone this project to your local machine (or simply create the project folder and files as described above).

Bash

git clone <your-repository-url>
cd change-management-chatbot
2. Set Up Your Google Gemini API Key
You'll need a Google API key to use the Gemini model.

Get your key from Google AI Studio.

In the root directory of the project, create a file named .env.

Add your API key to the .env file like this:

GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
3. Install Dependencies
Install all the required Python packages using pip. It's recommended to do this within a virtual environment.

Bash

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install packages
pip install Flask langchain-google-genai langchain-community chromadb pypdf python-dotenv
4. Add Your Knowledge Base
Place your own change management SOPs, FAQs, or any other relevant documents in PDF format inside the docs/ directory. The chatbot will learn from these files when it starts.

5. Run the Application
Start the Flask server from your terminal:

Bash

python app.py
You should see output indicating that the server is running and the RAG chain has been initialized.

6. Open the Chatbot
Open your web browser and navigate to: http://127.0.0.1:5000

You can now start chatting with your assistant!

💡 How It Works
This chatbot uses a modern AI architecture called Retrieval-Augmented Generation (RAG).

Loading & Chunking: When the server starts, it loads all documents from the docs/ folder and splits them into smaller, manageable chunks.

Embedding & Storing: Each chunk of text is converted into a numerical representation (an embedding) and stored in a ChromaDB vector database.

User Query: When you ask a question, the system first looks at the chat history to see if it's a follow-up question. It rephrases your question into a standalone query if needed.

Retrieval: The system searches the vector database to find the text chunks that are most relevant to your question.

Generation: The original question, chat history, and the retrieved text chunks are sent to the Gemini Pro model with a detailed prompt. The AI then generates a natural language answer based only on the information it was given.

This process ensures the chatbot's answers are grounded in your specific documentation and reduces the risk of AI "hallucinations."
