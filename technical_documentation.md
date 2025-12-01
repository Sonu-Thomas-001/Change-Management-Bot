# Change Management Chatbot - Technical Documentation

## 1. Introduction
The Change Management Chatbot is an intelligent assistant designed to streamline IT Service Management (ITSM) processes, specifically focusing on Change Management within ServiceNow. It leverages Generative AI (Google Gemini) and Retrieval-Augmented Generation (RAG) to provide context-aware answers, automate tasks, and assist users in managing change requests.

## 2. Technology Stack

### Backend
*   **Language:** Python 3.x
*   **Framework:** Flask (Web Server)
*   **AI/LLM Orchestration:** LangChain
*   **LLM Provider:** Google Gemini (`gemini-2.5-flash`)
*   **Vector Store:** ChromaDB (Local vector database for RAG)
*   **Integrations:** ServiceNow REST API

### Frontend
*   **Core:** HTML5, CSS3, JavaScript (Vanilla)
*   **Styling:** Custom CSS (Responsive design)
*   **Charts:** Chart.js (for Analytics)

### Data & Storage
*   **Knowledge Base:** PDF Documents (SOPs, Policies) stored in `docs/`
*   **Templates:** CSV file (`docs/change_templates.csv`) and ServiceNow `sys_template` table
*   **Logs:** CSV files for interaction logs, feedback, and escalations (`logs/`)

## 3. System Architecture

The application follows a modular Service-Oriented Architecture (SOA):

1.  **Presentation Layer (Routes):** `app/routes.py` handles HTTP requests, manages sessions, and routes user inputs to appropriate services.
2.  **Service Layer:** Contains the core business logic.
    *   `rag_service.py`: Manages the RAG chain, intent classification, and LLM interactions.
    *   `ticket_service.py`: Handles ServiceNow ticket retrieval and formatting.
    *   `smart_change_creator.py`: Logic for finding similar changes and creating/cloning tickets.
    *   `data_service.py`: General ServiceNow data fetching (stats, lists).
    *   `email_service.py`: Generates email drafts.
    *   `validator_service.py`: Validates emergency changes.
3.  **Data Layer:** Connects to ServiceNow via REST API and local CSV/PDF files.

## 4. Features & End-to-End Flow

### 4.1. Intelligent Intent Classification
*   **How it works:** Every user query is passed to an LLM-based classifier (`rag_service.classify_intent`).
*   **Categories:** The system categorizes queries into 12 distinct intents (e.g., `TICKET_STATUS`, `CREATE_CHANGE`, `RISK_ANALYSIS`, `SCHEDULE_QUERY`).
*   **Flow:** User Query -> LLM Classifier -> Intent Label -> Route Handler -> Specific Service -> Response.

### 4.2. Ticket Status & Insights (`TICKET_STATUS`)
*   **Feature:** Retrieves detailed status of a Change Request (CR).
*   **Capabilities:**
    *   Shows standard details (State, Risk, Priority).
    *   **Insightful View:** Checks for SLA breaches, pending approvers, and conflicts with other changes.
    *   **SLA Warning:** Calculates time since last update to flag potential delays.
*   **Flow:** Extract Ticket # (Regex) -> Fetch Details (ServiceNow) -> Check Conflicts/SLA -> Format Response.

### 4.3. Smart Change Creation (`CREATE_CHANGE`)
*   **Feature:** Assists in creating new change requests.
*   **Modes:**
    *   **Smart Clone:** Finds a similar past successful change and clones it.
    *   **Template Suggestion:** Suggests relevant templates based on natural language description.
*   **Flow:**
    1.  User says "Create change for Oracle update".
    2.  Bot asks: "Clone sample" or "Use Template"?
    3.  **Clone Path:** Search past changes -> Show Best Match -> User Confirms -> Create New CR (ServiceNow).
    4.  **Template Path:** RAG Search (CSV/ServiceNow) -> Recommend Template -> User Confirms -> Create New CR.

### 4.4. RAG-Based Q&A (General & Policy)
*   **Feature:** Answers questions based on uploaded PDF documents (SOPs).
*   **Multi-language:** Automatically detects user language and translates the answer.
*   **Personality:** Adapts tone based on user role (Admin vs. Standard User).

### 4.5. Risk Analysis (`RISK_ANALYSIS`)
*   **Feature:** Analyzes an implementation plan against SOPs to predict risk.
*   **Flow:** User Input (Plan) -> Retrieve relevant SOPs (RAG) -> LLM Assessment -> Risk Score & Missing Steps.

### 4.6. Analytics Dashboard
*   **Feature:** Visualizes chatbot usage and ServiceNow trends.
*   **Data:** Reads from local CSV logs and ServiceNow API.
*   **Charts:** Daily volume, Success rate, User satisfaction, Top keywords.

## 5. Deep Dive: How RAG (Retrieval-Augmented Generation) Works

The RAG system is implemented in `app/services/rag_service.py`.

### 5.1. Initialization (Ingestion)
1.  **Loading:** `PyPDFDirectoryLoader` loads PDFs from `docs/`. `CSVLoader` loads templates.
2.  **Splitting:** `RecursiveCharacterTextSplitter` breaks text into chunks (Size: 300, Overlap: 150).
3.  **Embedding:** `GoogleGenerativeAIEmbeddings` converts text chunks into vector embeddings.
4.  **Storage:** Embeddings are stored in a local **ChromaDB** vector store.

### 5.2. Retrieval
1.  **Query Contextualization:** If a chat history exists, the user's query is rewritten to be standalone (e.g., "It" -> "The Oracle Database").
2.  **Vector Search:** The system searches ChromaDB for the most similar document chunks to the query.
3.  **Template Retrieval:** A separate retriever is used for finding templates from the CSV.

### 5.3. Generation
1.  **Prompting:** A rich system prompt is constructed containing:
    *   **Persona:** (Expert vs. Helper).
    *   **Context:** The retrieved document chunks.
    *   **Rules:** Strict instructions on language detection, formatting, and honesty.
2.  **LLM Call:** The prompt + user query is sent to **Gemini-2.5-Flash**.
3.  **Response:** The LLM generates the answer, citing sources if defined in the prompt.

## 6. Function Calling & Routing Structure

The chatbot does not use native "Function Calling" APIs (like OpenAI's specific tool format) but implements a **Router-Controller Pattern**:

1.  **Entry Point:** `/ask` endpoint in `routes.py`.
2.  **Classification:** `rag_service.classify_intent(question)` is called first.
    *   *Input:* "What is the status of CR-100?"
    *   *Output:* `TICKET_STATUS`
3.  **Routing Logic:** A large `if-elif` block in `routes.py` directs the flow based on the intent.
    *   `if intent == "TICKET_STATUS":` -> Call `ticket_service.get_ticket_details`.
    *   `if intent == "CREATE_CHANGE":` -> Call `smart_change_creator` logic.
    *   `if intent == "RISK_ANALYSIS":` -> Call `rag_service.analyze_risk_score`.
4.  **Fallback:** If no specific intent matches (or intent is `GENERAL_QUERY`), it falls back to the standard RAG chain (`rag_service.answer_question`).

## 7. Key Files Overview

| File | Purpose |
| :--- | :--- |
| `run.py` | Entry point to start the Flask server. |
| `app/routes.py` | Main controller. Handles web requests and routes intents. |
| `app/services/rag_service.py` | Core AI logic. RAG setup, Intent Classification, Risk Analysis. |
| `app/services/ticket_service.py` | ServiceNow integration for fetching and formatting ticket data. |
| `app/services/smart_change_creator.py` | Logic for "Smart Clone" and "Template Suggestion". |
| `app/config.py` | Configuration settings (API Keys, Database credentials). |
| `app/static/script.js` | Frontend logic for chat interface and API calls. |
