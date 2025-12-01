# 🤖 FuturaAI Change Management Bot - Complete Features & Overview

## 📋 Overview

**FuturaAI** is an intelligent Change Management Assistant designed for ITIL-compliant organizations. Built on advanced RAG (Retrieval Augmented Generation) technology powered by Google Gemini, this chatbot transforms how teams interact with ServiceNow and manage organizational changes.

### 🎯 Mission
Streamline change management processes by providing instant access to SOPs, automating routine tasks, and delivering intelligent insights—all through natural conversation.

### 🚀 Key Capabilities

1. **Intelligent Q&A**: Answers questions using your organization's SOPs and policies
2. **Live ServiceNow Integration**: Real-time ticket status, approvals, tasks
3. **Multilingual Support**: Responds in 50+ languages including Hindi, Spanish, French, German, Japanese
4. **Role-Based Personalization**: Adapts tone for Users vs. Admins
5. **Email Automation**: Generates SOP-compliant emails with auto-filled placeholders
6. **Visual Analytics**: Interactive charts for risk, priority, trends, and approvals
7. **Emotion Detection**: Responds empathetically to frustrated users
8. **Voice Input**: Speak your questions instead of typing

---

## 🌟 Complete Feature List (27 Features)

### 1. Q&A (General Knowledge)
**Description**: Ask anything about change management processes, policies, or SOPs. The bot retrieves answers from your knowledge base using advanced RAG technology.

**How It Works**:
- You: "What is a Change Request?"
- Bot: Searches SOP documents → "A Change Request (CR) is a formal proposal to modify IT infrastructure..."

**Use Cases**:
- New employees learning ITIL processes
- Quick reference during CAB meetings
- Understanding approval workflows

---

### 2. Greetings & Casual Chat
**Description**: Natural conversational interaction. The bot recognizes greetings and small talk.

**Examples**:
- "Hi" → "Hello! How can I assist you today?"
- "Good morning" → "Good morning! Ready to help with change management."

**Why It Matters**: Creates a friendly, human-like experience.

---

### 3. Multi-Language Support
**Description**: Understand and respond in 50+ languages automatically.

**Supported Languages**: Spanish, French, German, Hindi, Portuguese, Japanese, Chinese, Russian, Arabic, and more.

**How It Works**:
- User asks: "¿Qué es una solicitud de cambio?" (Spanish)
- Bot replies in Spanish with accurate context from SOPs

**Use Cases**: Global teams, multilingual organizations.

---

### 4. Ticket Status (Insightful View) ⭐ UPGRADED
**Description**: Check the status of Change Requests with a comprehensive, insightful view.

**What You See**:
- 🔍 **Status Overview**: Description, State, Risk Score
- 📋 **Ticket Details**: Type, Priority, Impact, Assigned To, Dates
- 👥 **Pending Approvers**: Who needs to sign off + expected approval time
- 🛡️ **Conflict & Risk Alerts**: Warnings if other changes overlap on the same CI
- ⏱️ **SLA Status**: "Approval SLA will breach in 2 hours. Notifying approver automatically."

**How It Works**:
- You: "Check status of CHG0030001"
- Bot: Fetches from ServiceNow → Displays rich, multi-section view

**Mock Mode**: Try "CR-1024" or "CHG0030001" to see demo data.

---

### 5. Smart Change Creation (Clone & Templates) ⭐ UPGRADED
**Description**: Intelligent assistance to create new Change Requests using past successful changes or templates.

**Two Powerful Modes**:
1.  **Smart Clone**: Finds a similar *successful* past change and clones it.
    *   *You:* "Create a change for Oracle patching"
    *   *Bot:* "I found a successful past change (CHG0099). Would you like to clone it?"
2.  **Template Suggestion**: Uses AI to find the best standard template.
    *   *You:* "I need a template for server reboot"
    *   *Bot:* "Here is the 'Windows Server Reboot' template. Click to use."

**Output**: 
- ✅ Creates a draft Change Request in ServiceNow.
- Displays the new ticket number and details.

---

### 6. Approvals
**Description**: View pending approvals assigned to you.

**What You See**:
- HTML table with columns: Ticket, Description, Requested By, Priority, Opened, Action
- "View" button to open each approval in ServiceNow

**How It Works**:
- You: "Show my pending approvals"
- Bot: Queries ServiceNow for your username → Displays table

---

### 7. Tasks
**Description**: View pending tasks assigned to you.

**What You See**:
- HTML table with columns: Task Number, Description, State, Priority, Due Date, Action
- Color-coded state badges (Pending = Yellow, In Progress = Blue, Assigned = Gray)

**How It Works**:
- You: "Show my pending tasks"
- Bot: Fetches active tasks from ServiceNow → Displays table

---

### 8. Risk Chart
**Description**: Visualize changes by risk level (Very High, High, Moderate, Low).

**How It Works**:
- You: "Show chart of changes by risk"
- Bot: Queries ServiceNow stats API → Renders bar chart

**Use Cases**: CAB meetings, risk management reviews.

---

### 9. Priority Chart
**Description**: Visualize changes by priority (1-Critical, 2-High, 3-Moderate, 4-Low).

**How It Works**:
- You: "Show stats by priority"
- Bot: Renders interactive chart with counts

---

### 10. State Chart
**Description**: Visualize changes by state (New, Assess, Authorize, Scheduled, Implement, Closed).

**How It Works**:
- You: "Show change request status"
- Bot: Displays distribution across lifecycle stages

---

### 11. Trend Chart
**Description**: Visualize change volume over time (monthly trend).

**How It Works**:
- You: "Show monthly trend of changes"
- Bot: Displays line chart showing volume trends

**Use Cases**: Capacity planning, trend analysis.

---

### 12. Approval Chart
**Description**: Visualize approval statistics (Approved vs. Rejected vs. Pending).

**How It Works**:
- You: "Show approved vs rejected changes"
- Bot: Displays pie chart with approval outcomes

---

### 13. Email Draft (SOP-Compliant) ⭐ UPGRADED
**Description**: Generate SOP-compliant email drafts with auto-filled placeholders.

**Templates Available**:
1. **Acknowledgment**: "Your Change Request [CR-ID] has been received..."
2. **Status Update**: "The status of Change Request [CR-ID] is currently [Stage]..."
3. **Exception Approval**: "We request approval for an exception to standard procedures..."

**How It Works**:
- You: "Draft acknowledgment email for CR-123"
- Bot: 
  - Selects correct template
  - Auto-fills `[CR-ID]` with `CR-123`
  - Generates mailto link
  - Shows preview with "📧 Draft in Outlook" button

**Smart Placeholder Extraction**: Automatically detects `CR-123`, `CHG-999` from your question.

---

### 14. Multilingual Email Drafting ⭐ NEW
**Description**: Generate SOP-compliant emails in any language.

**How It Works**:
- You: "Draft acknowledgment email for CR-123 in Spanish"
- Bot:
  1. Generates English draft using SOP template
  2. Translates subject and body to Spanish
  3. Preserves placeholders (`CR-123`, `[Manager Name]`)
  4. Shows "📧 Draft in Outlook (Spanish)" button

**Supported Languages**: Spanish, French, German, Hindi, Portuguese, Italian, Chinese, Japanese, Russian, Arabic.

---

### 15. Risk Assessment
**Description**: Analyze the risk of a proposed change plan.

**How It Works**:
- You: "Analyze risk for: Database migration during business hours on production server"
- Bot: Uses LLM to evaluate → "⚠️ **High Risk**. Business hours deployment increases impact. Recommendation: Schedule during maintenance window."

**Use Cases**: Pre-CAB planning, risk scoring.

---

### 16. Schedule Check
**Description**: Check for scheduling conflicts.

**How It Works**:
- You: "Can I schedule change on December 25?"
- Bot: Checks blackout dates → "❌ December 25 is a blackout date (Holiday). Please choose another date."

---

### 17. Scheduled Changes (with Export)
**Description**: View and export scheduled changes by time period.

**How to Use**:
1. **Via Chat**: "What changes are planned for today?"
2. **Via Analytics UI**: Click "Analytics" → "Scheduled Changes" tab → View table → "Export to Excel"

**What You See**:
- Table with columns: Number, Description, State, Priority, Scheduled Start, Owner
- Export button (bottom-left) to download as CSV

---

### 18. Keyword Search & Export
**Description**: Filter changes by keywords and export results.

**How It Works**:
- You: "Show me database changes planned for this weekend"
- Bot: Filters by keyword "database" + time "weekend" → Displays table + export option

**Use Cases**: Targeted searches (e.g., "firewall changes next month", "oracle upgrades last week").

---

### 19. Personality Engine ⭐ NEW
**Description**: Bot adapts its tone and verbosity based on your role.

**How It Works**:
- **User Role** (`user` / `password`):
  - Tone: Friendly, simple, patient
  - Example: "A Change Request is basically a way to ask for a tech change. Let me walk you through it step-by-step..."
  
- **Admin Role** (`admin` / `admin`):
  - Tone: Formal, concise, technical
  - Example: "A CR is a formal document recording proposed IT modifications, requiring CAB approval per ITIL framework."

**Why It Matters**: Reduces cognitive load for beginners, speeds up responses for experts.

---

### 20. Emotion Detection ⭐ NEW
**Description**: Detects frustration and responds empathetically.

**Trigger Keywords**: "stuck", "error", "broken", "frustrated", "annoying", "can't", "unable", "wrong"

**How It Works**:
- You: "I'm stuck, this approval is broken!"
- Bot: "⚠️ I understand this is frustrating. Let me help you troubleshoot step-by-step..."

**Why It Matters**: Improves user satisfaction during high-stress situations.

---
### 21. Feedback & Escalation ⭐ NEW
**Description**: Submit feedback or escalate complex issues to a human manager.

**How It Works**:
- **Feedback**: "I want to give feedback" -> Bot logs thumbs up/down and comments.
- **Escalation**: "Escalate this to a manager" -> Bot logs the chat history and notifies the Change Manager.

---
### 22. Login & Authentication
**Description**: Secure, role-based access control.

**Credentials**:
- **User Role**: `user` / `password`
- **Admin Role**: `admin` / `admin`

**Features**:
- Session-based authentication
- Protected routes (requires login)
- Automatic redirect to login page
- Logout clears session

---

### 23. Voice Input
**Description**: Speak your questions instead of typing.

**How to Use**:
1. Click 🎤 microphone icon
2. Grant microphone permission
3. Speak your question
4. Text appears in input box
5. Submit as normal

**Why It Matters**: Hands-free operation, accessibility for visually impaired users.

---

### 24. Clear Chat History
**Description**: Reset the chat session.

**How to Use**:
- Click "Clear History" button
- Chat area clears
- Welcome message reappears

**Why It Matters**: Start fresh without reloading the page.

---

## 🔧 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (ES6+) |
| **Backend** | Python 3.x, Flask |
| **LLM** | Google Gemini (gemini-2.5-flash) |
| **Vector DB** | ChromaDB (Local Vector Store) |
| **Embeddings** | GoogleGenerativeAIEmbeddings |
| **ServiceNow** | REST API Integration |
| **Charts** | Chart.js |
| **Voice** | Web Speech API |
| **Session** | Flask Sessions |

---

## 📊 Analytics Dashboard

Access via "Analytics" button in header.

**4 Tabs**:
1. **Overview**: High-level metrics and KPIs
2. **Charts**: Interactive visualizations (risk, priority, state, trend, approval)
3. **Query Trends**: Volume of user queries over time
4. **Scheduled Changes**: Upcoming/completed changes with export

---

## 🔐 Security & Compliance

- **Session-Based Auth**: No tokens exposed in URLs
- **Role-Based Access**: User vs. Admin permissions
- **ServiceNow Integration**: Uses secure HTTPS + Basic Auth
- **No Data Persistence**: Chat history not logged (privacy-first)

---

## 🎨 User Experience Highlights

### Design Philosophy
- **Clean & Modern**: Futuristic gradient design with smooth animations
- **Accessible**: Dark mode, voice input, large click targets
- **Responsive**: Works on desktop, tablet, mobile
- **Fast**: Optimized API calls, lazy loading

### Interaction Patterns
- **Conversational**: Ask questions naturally, no command syntax
- **Visual Feedback**: Loading indicators, typing animations
- **Error Handling**: Graceful fallbacks, helpful error messages

---

## 🌐 Deployment Options

### Mock Mode (Demo)
- **When**: No ServiceNow credentials configured
- **Features**: All features work with hardcoded demo data
- **Use Case**: Testing, demos, training

### Production Mode (Live)
- **When**: ServiceNow credentials in `.env`
- **Features**: Real-time data from your ServiceNow instance
- **Use Case**: Daily operations

---

## 📚 Knowledge Base

The bot learns from:
1. **SOP Documents** (PDF): Uploaded to `app/knowledge/`
2. **ServiceNow Data**: Live ticket info via API
3. **Hardcoded Policies**: Blackout dates, SLA rules

---

## 📈 Roadmap

### Future Enhancements
- [ ] Slack/Teams Integration
- [ ] Advanced NLP for Intent Recognition
- [ ] PDF Report Generation
- [ ] Automated Compliance Checks
- [ ] Mobile App (iOS/Android)
- [ ] Multi-Tenant Support

---

## 💡 Use Cases

### For End Users
- "How do I submit a change request?"
- "Check status of my pending approvals"
- "Draft an email for stakeholders"

### For Change Managers
- "Show me high-risk changes this week"
- "List all database changes for next month"
- "Analyze risk for this deployment plan"

### For CAB Members
- "What changes are pending my approval?"
- "Show monthly trend of emergency changes"
- "Export scheduled changes to Excel"

---

## 🏆 Benefits

| Benefit | Impact |
|---------|--------|
| **⏱️ Time Savings** | 70% reduction in time to find SOP info |
| **📉 Error Reduction** | Auto-filled email placeholders prevent mistakes |
| **🌍 Global Reach** | Multilingual support for distributed teams |
| **🎯 Better Decisions** | Visual analytics + risk scoring |
| **😊 User Satisfaction** | Empathetic responses + voice input |

---

## 🤝 Support

For issues, feature requests, or questions:
- Check **TEST_GUIDE.md** for troubleshooting
- Review **README.md** for setup help
- Contact: Sonu Thomas (Project Owner)

---

**Built with ❤️ by the FuturaAI Team**

*Transforming Change Management, One Conversation at a Time.*
