<div align="center">

  <h1>🤖 Change Management Assistant</h1>
  
  <p>
    <strong>An AI-powered RAG Chatbot for Enterprise SOPs</strong>
  </p>

  <p>
    <a href="#-key-features">Key Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-installation">Installation</a> •
    <a href="#-usage">Usage</a> •
    <a href="#-project-structure">Structure</a>
  </p>

  ![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
  ![Flask](https://img.shields.io/badge/Flask-Server-000000?style=for-the-badge&logo=flask&logoColor=white)
  ![LangChain](https://img.shields.io/badge/LangChain-RAG-green?style=for-the-badge)
  ![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

</div>

---

## 📖 Overview

The **Change Management Assistant** is an intelligent, conversational chatbot designed to streamline information retrieval from dense Standard Operating Procedure (SOP) documents. 

Built on a **Retrieval-Augmented Generation (RAG)** architecture, it allows employees to ask questions in plain English and receive instant, accurate answers sourced **strictly** from official documentation. This eliminates manual searching, ensures procedural consistency, and reduces the support burden on IT teams.

---

## ✨ Key Features

### 🧠 Intelligent AI Core
* **Source-Based Accuracy:** Answers are generated *only* from your uploaded PDF documents (SOPs, Policies). Zero hallucinations.
* **Conversational Memory:** The bot remembers context, allowing for natural follow-up questions.
* **Semantic Search:** Uses vector embeddings (`ChromaDB`) to understand the *meaning* of questions, not just keywords.

### 💻 Modern User Interface
* **Rich Formatting:** Responses include **Bold text**, *Bullet points*, and **Tables** for readability.
* **Voice Interaction:** Integrated **Speech-to-Text** allows hands-free querying.
* **Export to PDF:** Download your entire conversation history for record-keeping.
* **Interactive Actions:** Copy responses, edit your queries, and clear chat history with one click.

### 📊 Analytics & Admin (RBAC)
* **Role-Based Access:** Separate views for **Employees** (Chat only) and **Admins** (Chat + Analytics).
* **Analytics Dashboard:** Tracks daily query trends, most asked questions, and user satisfaction.
* **Gap Analysis:** Automatically logs "Unanswered Questions" to highlight missing info in your SOPs.
* **User Feedback:** Built-in Thumbs Up/Down mechanism to track response quality.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Flask |
| **Orchestration** | LangChain |
| **LLM** | Google Gemini 1.5 Flash |
| **Embeddings** | HuggingFace (Local) / Google Generative AI |
| **Vector Store** | ChromaDB (Local) |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Utilities** | PyPDF, Marked.js, Chart.js, HTML2PDF |

---

## 🚀 Installation

Follow these steps to run the project locally.

### 1. Clone the Repository
```bash
git clone [https://github.com/YourUsername/Change-Management-Bot.git](https://github.com/YourUsername/Change-Management-Bot.git)
cd Change-Management-Bot
