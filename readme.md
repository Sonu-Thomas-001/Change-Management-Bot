<div align="center">

  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:000000,100:2c3e50&height=300&section=header&text=Change%20Management%20Assistant&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Enterprise%20SOP%20Intelligence%20%7C%20Powered%20by%20Gemini%20AI&descAlignY=55&descAlign=50" alt="Change Management Assistant Header" width="100%"/>

  <br/>

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-Server-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
  [![Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
  [![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF5F00?style=for-the-badge)](https://www.trychroma.com/)
  [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

  <br/>
  
  <p align="center">
    <a href="#-vision">Vision</a> •
    <a href="#-intelligence">Intelligence</a> •
    <a href="#-auditor-core">Auditor Core</a> •
    <a href="#-deployment">Deployment</a> •
    <a href="#-roadmap">Roadmap</a>
  </p>

</div>

---

## 🌌 Vision

The **Change Management Assistant** is not just a chatbot; it's a **cognitive layer** for your organizational knowledge. 

By fusing **Retrieval-Augmented Generation (RAG)** with **Agentic Workflows**, it transforms static, dusty PDF documents into a living, breathing expert system. It doesn't just answer questions—it **audits processes**, **identifies gaps**, and **secures compliance** in real-time.

> *"The future of work is not searching for answers, but having them delivered before you ask."*

---

## 🧠 Intelligence Architecture

### **Core Cognitive Engine**
| Component | Technology | Role |
| :--- | :--- | :--- |
| **LLM** | `Google Gemini 1.5 Flash` | The reasoning brain. Fast, multimodal, and context-aware. |
| **Memory** | `ChromaDB` (Local) | Vector storage for semantic search and retrieval. |
| **Orchestrator** | `LangChain` | Manages the flow between user, data, and AI. |
| **Embeddings** | `HuggingFace` | Privacy-first, local text-to-vector conversion. |

### **Key Capabilities**
*   **Zero-Hallucination RAG:** Answers are strictly grounded in your provided documentation.
*   **Role-Based Neural Access:** Adapts responses based on user hierarchy (Employee vs. Admin).
*   **Self-Healing Knowledge:** Automatically flags "Unanswered Questions" to highlight SOP gaps.

---

## ⚙️ Mechanics: The Lifecycle of a Query

Understanding the flow of intelligence within the system.

### **1. Knowledge Ingestion (The Learning Phase)**
Before the bot answers a single question, it must "learn" your SOPs.
1.  **Extraction:** `PyPDFLoader` strips text from your PDF documents in `/docs`.
2.  **Chunking:** The text is split into manageable "cognitive blocks" (1000 characters) with overlap to preserve context.
3.  **Vectorization:** `HuggingFaceEmbeddings` converts these text blocks into 384-dimensional vector arrays (mathematical representations of meaning).
4.  **Storage:** These vectors are indexed in `ChromaDB` for millisecond-latency retrieval.

### **2. The Neural Router (The Decision Phase)**
When a user types a message, the **Intent Recognition Engine** analyzes the semantic intent:
*   **Intent: "Audit..."** → Routes to **Auditor Core** for SQL-like ticket analysis.
*   **Intent: "Show me..."** → Routes to **Analytics Engine** for data visualization.
*   **Intent: "How do I..."** → Routes to **RAG Engine** for knowledge retrieval.

### **3. Retrieval & Synthesis (The Answering Phase)**
If routed to the RAG Engine:
1.  **Query Embedding:** The user's question is converted into a vector.
2.  **Semantic Search:** The system scans `ChromaDB` for the top 3 most similar document chunks.
3.  **Context Injection:** These chunks are appended to a strict "System Prompt" that forbids hallucination.
4.  **Generation:** `Gemini 1.5 Flash` synthesizes the retrieved facts into a coherent, human-like answer.
5.  **Citation:** The source document and page number are appended to the final response.

---

## 🚨 Auditor Core: The Compliance Sentinel

A state-of-the-art module designed to enforce SOPs automatically.

<div align="center">
  <table>
    <tr>
      <td align="center"><strong>⚡ Instant Audit</strong></td>
      <td align="center"><strong>🚦 Visual Reporting</strong></td>
      <td align="center"><strong>📥 Data Extraction</strong></td>
    </tr>
    <tr>
      <td>Analyzes emergency tickets in milliseconds against strict policy rules.</td>
      <td>Generates beautiful, traffic-light coded HTML reports instantly.</td>
      <td>One-click export to <code>.csv</code> for deep-dive analytics.</td>
    </tr>
  </table>
</div>

**Usage:**
> User: *"Audit all emergency changes from yesterday"*
>
> **Bot:** *Scans tickets... Checks Priority... Verifies Justification...* -> **Generates Report**

---

## 💻 Modern Experience

We believe enterprise tools should feel like consumer apps.

*   **Glassmorphism UI:** A clean, modern interface designed for focus.
*   **Voice-First Interaction:** Integrated Speech-to-Text for hands-free operation.
*   **Dynamic Analytics Dashboard:**
    *   *Query Volume Trends*
    *   *Sentiment Analysis (Thumbs Up/Down)*
    *   *Topic Word Clouds*

---

## 🚀 Deployment Protocol

### **Prerequisites**
*   Python 3.10+
*   Google Gemini API Key

### **Sequence**

```bash
# 1. Clone the Neural Network
git clone https://github.com/YourUsername/Change-Management-Bot.git
cd Change-Management-Bot

# 2. Initialize Virtual Environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Inject Credentials
# Create .env file: GOOGLE_API_KEY="your_key_here"

# 5. Ingest Knowledge
# Place PDF SOPs into /docs folder

# 6. Ignite System
python app.py
```

---

## �️ Security Protocol

In an era of data sovereignty, privacy is paramount.

*   **Local Vectorization:** All document embeddings are generated locally using `HuggingFace` models. Your proprietary SOPs never leave your server during indexing.
*   **Ephemeral Context:** User queries are processed in-memory.
*   **RBAC Enforcement:** Strict logical separation between `Employee` and `Admin` capabilities.

---

## 🔧 Troubleshooting & Diagnostics

**System not igniting?**

*   **Error:** `GoogleGenAIError: Invalid API Key`
    *   *Fix:* Ensure your `.env` file is present and the key is valid.
*   **Error:** `ChromaDB Connection Failed`
    *   *Fix:* Delete the `chroma_db` folder to force a fresh re-indexing of your documents.
*   **Issue:** "The bot is hallucinating."
    *   *Fix:* The RAG temperature is set to `0.3` for precision. Ensure your PDF contains the specific answer.

---

## 🤝 Contributing to the Hive

We welcome architects of the future.

1.  **Fork** the neural repository.
2.  **Branch** your feature (`git checkout -b feature/neural-upgrade`).
3.  **Commit** your enhancements.
4.  **Push** and open a **Pull Request**.

---

We are building the autonomous enterprise.

- [ ] **Neural Hive Mind:** Active Directory (SSO) Integration for seamless identity.
- [ ] **Knowledge Osmosis:** Admin Portal for drag-and-drop PDF ingestion.
- [ ] **Omnichannel Presence:** Native integration with MS Teams & Slack.
- [ ] **Hyper-Specialization:** Fine-tuning Gemini on your specific industry jargon.

---

<div align="center">
  <br/>
  <sub>Designed & Engineered for the Future of Work.</sub>
  <br/>
  <sub>Built with ❤️ using <strong>Python</strong>, <strong>LangChain</strong>, and <strong>Gemini</strong>.</sub>
</div>
