# � Futura.ai Chatbot Test Guide

This document provides a structured guide for testing the features of the Futura.ai Change Management Bot.

---

## 1. General Queries (Change Management Process)
**Objective**: Verify the bot can answer general process questions using its Knowledge Base (RAG).

*   **Test 1**: "What is the process for creating an emergency change request?"
*   **Test 2**: "How do I request a CAB meeting for my change?"
*   **Test 3**: "Explain the difference between a Normal and Standard change."

## 2. Template Identification & Suggestions
**Objective**: Verify the bot can find relevant templates and similar past changes.

*   **Test 1**: "Find a template for a database server upgrade."
*   **Test 2**: "Show me similar past changes related to 'Firewall Rule Update'."
*   **Test 3**: "Suggest a template for decommissioning a legacy server."

## 3. Multilanguage Support
**Objective**: Verify the bot can understand and respond in different languages.

*   **Test 1**: "Hola, ¿cómo creo un ticket de cambio?" (Spanish)
*   **Test 2**: "Draft an email for maintenance in French."
*   **Test 3**: "Erklären Sie den Änderungsprozess." (German - Explain the change process)

## 4. Smart Change Creation
**Objective**: Verify the bot's ability to simplify change creation through suggestions, cloning, and drafting.

### a. Smart Suggestions (Discovery)
*   **Test 1**: "Create a change for upgrading the firewall." (Expect: Bot suggests a similar past change to clone)
*   **Test 2**: "I need to reboot the primary server." (Expect: Bot finds a relevant template or past change)
*   **Test 3**: "Plan a database maintenance for next week." (Expect: Bot offers to clone a previous maintenance ticket)

### b. Change Cloning (Action)
*   **Test 1**: "Clone CHG0000001 for next Friday." (Expect: New ticket created with copied details and new date)
*   **Test 2**: "Copy change CHG0000002 and assign it to me." (Expect: New ticket assigned to current user)
*   **Test 3**: "Duplicate the last change for 'Network Switch Upgrade'." (Expect: Bot identifies the last relevant change and clones it)

### c. Email Drafting (Communication)
*   **Test 1**: "Draft an email for upcoming database downtime." (Expect: Professional email draft with placeholders)
*   **Test 2**: "Write a notification for a security patch deployment in Spanish." (Expect: Translated email draft)
*   **Test 3**: "Create a communication draft for emergency network maintenance explaining the impact." (Expect: Detailed impact communication)

## 5. Ticket Status & Quality
**Objective**: Verify retrieval of ticket details, approvals, and quality checks.

### a. Change Request Status
*   **Test 1**: "Check the status of CHG0000001."
*   **Test 2**: "What is the current state of my last created ticket?"
*   **Test 3**: "Show details for CHG0000002."

### b. Approval Status
*   **Test 1**: "Show my pending approvals."
*   **Test 2**: "Do I have any approvals waiting for me?"
*   **Test 3**: "Check approval status for CHG0000001."

### c. Graphical Visualization
*   **Test 1**: "Show me a pie chart of change risks."
*   **Test 2**: "Visualize change priorities for this month."
*   **Test 3**: "Display a bar chart of change states."

### d. Change Quality (SOP/KB)
*   **Test 1**: "Does this description meet the SOP guidelines: 'Fixing server'?"
*   **Test 2**: "Validate if my change plan follows the standard process."
*   **Test 3**: "Check this change against the Knowledge Base best practices."

### e. Risk Identification
*   **Test 1**: "Analyze the risk for this change: 'Rebooting the core production switch during business hours'."
*   **Test 2**: "What is the risk level for 'Updating the employee cafeteria menu'?"
*   **Test 3**: "Identify potential risks for 'Migrating the primary database to the cloud'."

## 7. Monthly Change Trend Chart
**Objective**: Verify the bot can generate trend analysis charts.

*   **Test 1**: "Show me the monthly change trend for this year."
*   **Test 2**: "Display the trend of changes over the last 6 months."
*   **Test 3**: "How has the change volume changed compared to last month?"

## 8. Analytic Dashboard
**Objective**: Verify access to the admin analytics dashboard.

*   **Test 1**: (Login as Admin) Navigate to the Analytics Dashboard page.
*   **Test 2**: "Show me the success rate of changes."
*   **Test 3**: "Who are the top change requestors this month?"

## 9. Conflict Detection
**Objective**: Verify the bot can identify scheduling conflicts.

*   **Test 1**: "Can I schedule a change for this Saturday?"
*   **Test 2**: "Are there any conflicts for 'Database Upgrade' on December 25th?"
*   **Test 3**: "Check availability for a maintenance window next Sunday at 2 AM."

## 10. Scheduled Changes
**Objective**: Verify filtering of the change schedule.

### a. Based on Time
*   **Test 1**: "What changes are planned for today?"
*   **Test 2**: "Show changes scheduled for next week."
*   **Test 3**: "List changes planned for this weekend."

### b. Based on Keywords
*   **Test 1**: "Show me all network-related changes."
*   **Test 2**: "List pending changes involving 'Oracle'."
*   **Test 3**: "Find changes related to 'Security Patch'."

### c. Based on Keyword & Time
*   **Test 1**: "Show network changes planned for next month."
*   **Test 2**: "List database changes scheduled for this weekend."
*   **Test 3**: "What security updates are happening tomorrow?"

## 11. Personality Engine (Role-Based Response)
**Objective**: Verify the bot adapts its tone based on the user role.

*   **Test 1**: (As User) "Hi, I need help understanding changes." (Expect: Friendly, simple, helpful)
*   **Test 2**: (As Admin) "Show me the performance stats." (Expect: Professional, data-driven, concise)
*   **Test 3**: "Explain the approval process." (Compare response between User and Admin roles)

## 12. Emotion Detection
**Objective**: Verify the bot responds appropriately to user sentiment.

*   **Test 1**: "I am very frustrated! This process is too complicated." (Expect: Empathetic, de-escalating)
*   **Test 2**: "Great job, that was exactly what I needed!" (Expect: Positive acknowledgement)
*   **Test 3**: "This is confusing and annoying." (Expect: Apologetic, offer of assistance)

## 13. Voice Input
**Objective**: Verify the microphone input functionality.

*   **Test 1**: Click the Microphone icon and say: "Show my pending tasks."
*   **Test 2**: Click the Microphone icon and say: "Create a change for server reboot."
*   **Test 3**: Click the Microphone icon and say: "What is the status of CHG0000001?"

## 14. Export Chat
**Objective**: Verify the ability to save the conversation.

*   **Test 1**: Click the "Export Chat" (or similar) button in the UI.
*   **Test 2**: "Export this conversation to PDF/Text."
*   **Test 3**: Verify the downloaded file contains the full chat history.

## 15. Clear History
**Objective**: Verify the ability to reset the conversation.

*   **Test 1**: Click the "Clear History" (Trash icon) button.
*   **Test 2**: "Clear my chat history."
*   **Test 3**: Refresh the page and confirm the previous conversation is gone.
