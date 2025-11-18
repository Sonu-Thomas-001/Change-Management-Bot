<div align="center">

  <h1>🤖 Change Management Assistant</h1>
  
  <p>
    <strong>An Enterprise-Grade AI Chatbot for SOP Intelligence</strong>
  </p>

  <p>
    <a href="#-overview">Overview</a> •
    <a href="#-key-features">Features</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-installation">Installation</a> •
    <a href="#-usage-guide">Usage</a>
  </p>

  ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Flask](https://img.shields.io/badge/Flask-Server-000000?style=for-the-badge&logo=flask&logoColor=white)
  ![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
  ![Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)
  ![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF5F00?style=for-the-badge)

</div>

---

## 📖 Overview

The **Change Management Assistant** is a secure, conversational AI tool designed to democratize access to complex organizational knowledge. 

By leveraging **Retrieval-Augmented Generation (RAG)**, it transforms static Standard Operating Procedure (SOP) documents into an interactive expert. Unlike standard search, it understands context, handles follow-up questions, and provides precise answers sourced **strictly** from approved documentation.

> **New in v2.0:** Now features Role-Based Access Control (RBAC), a full Analytics Dashboard, and Local Embeddings for enhanced privacy and speed.

---

## ✨ Key Features

### 🧠 **AI & Intelligence**
* **RAG Architecture:** Grounds answers in your specific PDF documents. Zero hallucinations.
* **Local Embeddings:** Uses `HuggingFace` embeddings locally on your CPU. Fast, free, and private.
* **Conversational Memory:** Remembers chat history for natural follow-up questions.
* **Source Citation:** Cites the specific document used for every answer.

### 🛡️ **Security & RBAC**
* **Role-Based Login:**
    * **Employees:** Access to Chat interface only.
    * **Admins:** Access to Chat + Analytics Dashboard.
* **Context-Aware Responses:** The AI adjusts its answer complexity based on the logged-in user's role.

### 📊 **Analytics & Insights**
* **Live Dashboard:** Visual trend charts of daily queries.
* **Gap Analysis:** Automatically logs "Unanswered Questions" to identify holes in your SOPs.
* **User Feedback:** Tracks "Thumbs Up/Down" ratings to measure satisfaction.
* **Trend Spotting:** Word cloud analysis of most frequently asked topics.

### 💻 **Modern UX/UI**
* **Rich Formatting:** Markdown support (Tables, **Bold**, Lists).
* **Voice Interaction:** Speech-to-Text integration for hands-free use.
* **Productivity Tools:** One-click **PDF Export** of chat history, **Copy** response, and **Edit** query.
* **Responsive Design:** Works seamlessly on Desktop and Mobile.

---
    
🚀 Installation
Prerequisites
Python 3.10+

A Google Gemini API Key (Get one here)

1. Clone the Repository
Bash

git clone [https://github.com/YourUsername/Change-Management-Bot.git](https://github.com/YourUsername/Change-Management-Bot.git)
cd Change-Management-Bot
2. Set Up Virtual Environment
Bash

# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Configure Environment
Create a file named .env in the root directory:

Ini, TOML

GOOGLE_API_KEY="paste_your_api_key_here"
5. Add Documents
Place your PDF files (SOPs, Policies) inside the docs/ folder.

⚡ Usage Guide
Start the Application
Bash

python app.py
Wait for the "Initializing RAG Chain..." message. The first run may take a moment to download the local embedding model.

1. Login
Navigate to http://127.0.0.1:5000.

Login as Employee: Access the chat interface to ask questions.

Login as Admin: Access the chat + the Analytics link in the header.

2. Chatting
Ask Questions: "What is the template for a software update?"

Voice: Click the 🎙️ icon to speak.

Edit: Click the ✏️ icon on your message to fix a typo.

Export: Click the 📄 icon in the header to download the chat as a PDF.

3. Analytics (Admin Only)
Click "📊 Analytics" in the header to view:

Total query volume vs. Unanswered queries.

Line chart of usage over time.

User satisfaction (Thumbs Up vs. Down).

Specific lists of gaps in your documentation.

📂 Project Structure
Plaintext

/Change-Management-Bot
│
├── app.py                 # Main Application Logic (Flask + RAG + Analytics)
├── requirements.txt       # Python Dependencies
├── .env                   # API Keys (Ignored by Git)
├── README.md              # Project Documentation
│
├── docs/                  # Knowledge Base
│   └── SOP.pdf            # Your Source Documents
│
├── static/                # Frontend Assets
│   ├── style.css          # Responsive Styling & Animations
│   └── script.js          # Logic for Chat, Voice, Feedback, PDF
│
└── templates/             # HTML Views
    ├── index.html         # Main Chat Interface
    ├── login.html         # Authentication Page
    └── analytics.html     # Admin Dashboard
🔮 Future Roadmap
[ ] Active Directory Integration: Replace simple login with true SSO (LDAP/OAuth).

[ ] Admin Upload Portal: Allow Admins to upload/delete PDFs via the UI.

[ ] Teams/Slack Integration: Deploy the bot where users work.

[ ] Fine-Tuning: Fine-tune the Gemini model on specific enterprise jargon.

<div align="center"> <sub>Built with ❤️ using Python, LangChain, and Gemini.</sub> </div>
