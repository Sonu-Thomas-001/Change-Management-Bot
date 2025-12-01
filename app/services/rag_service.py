import os
from flask import jsonify
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFDirectoryLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config import Config
from app.services.data_service import get_recent_changes_by_keyword

# Global State
rag_chain = None
llm = None
retriever = None
template_retriever = None

def initialize_rag_chain():
    global rag_chain, llm, retriever, template_retriever
    try:
        print("Initializing RAG Chain...")
        
        # --- 1. Load PDFs for Knowledge Base ---
        loader = PyPDFDirectoryLoader("docs")
        documents = loader.load()
        if not documents:
            print("Warning: No PDF documents found in 'docs/' folder.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)
        print(f"Processed {len(docs)} document chunks.")

        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings, collection_name="kb_collection")
        retriever = vectorstore.as_retriever()
        
        # --- 2. Load CSV for Templates ---
        csv_path = os.path.join("docs", "change_templates.csv")
        if os.path.exists(csv_path):
            print("Loading Template CSV...")
            csv_loader = CSVLoader(file_path=csv_path, encoding="utf-8-sig")
            template_docs = csv_loader.load()
            
            # Create a separate vector store for templates
            template_vectorstore = Chroma.from_documents(
                documents=template_docs, 
                embedding=embeddings,
                collection_name="template_collection"
            )
            # Increase k to retrieve more potential matches (user requested "all relevant")
            template_retriever = template_vectorstore.as_retriever(search_kwargs={"k": 15})
            print(f"Processed {len(template_docs)} template rows.")
        else:
            print("Warning: Template CSV not found.")
        
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

        qa_system_prompt = (
            "You are the 'Change Management Assistant', a professional AI chatbot. "
            "Your purpose is to answer questions about change management based on the provided context. "
            "Your knowledge base consists of multiple documents (SOPs, Policies, KB Articles).\n\n"
            
            "--- PERSONALITY & TONE ---\n"
            "{persona}\n"
            "{emotion_context}\n\n"

            "--- MULTI-LANGUAGE RULES (CRITICAL) ---\n"
            "1. **Detect Language:** Automatically detect the language of the user's question.\n"
            "2. **Respond in Kind:** You MUST answer in the EXACT SAME language as the user's question. (e.g., If user asks in Hindi, answer in Hindi).\n"
            "3. **Context Translation:** The provided context is in English. You must translate the relevant information from the context into the user's language to answer.\n\n"

            "--- BEHAVIORAL RULES ---\n"
            "1. **Greeting:** Respond naturally to greetings in the user's language.\n"
            "2. **Identity:** If asked who you are, introduce yourself as 'Change Management Assistant' (translated if needed).\n"
            "3. **Knowledge-Based Questions:** Answer based ONLY on the provided context below. Do not make up information.\n"
            "4. **No Context:** If the answer is not in the context, apologize and state you don't have information, BUT translate this refusal message into the user's language.\n"
            "5. **Formatting:** Use **Bold**, *Bullets*, and **Tables** for readability.\n"
            "6. **Source Citation:** At the end, mention the source document: *(Source: Document Name)*.\n"
            "7. **Conflict Handling:** If you find conflicting information, mention both.\n\n"

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

def detect_emotion(query):
    """
    Detects frustration or negative emotion in the user's query.
    """
    query_lower = query.lower()
    triggers = [
        "stuck", "error", "fail", "broken", "not working", "frustrated", 
        "annoying", "help", "confused", "wrong", "unable", "can't", "cannot"
    ]
    
    if any(trigger in query_lower for trigger in triggers):
        return "⚠️ USER SEEMS FRUSTRATED. Be empathetic, patient, and reassuring. Start by acknowledging their difficulty."
    return ""

def answer_question(question, chat_history, user_role="User"):
    """
    Invokes the RAG chain with dynamic personality and emotion context.
    """
    if not rag_chain:
        return {"answer": "System is initializing, please try again in a moment."}

    # 1. Determine Persona
    if user_role == "Change Admin":
        persona = (
            "**ROLE:** You are speaking to a **Change Administrator** (Expert). "
            "Be concise, professional, and technical. Focus on efficiency, compliance, and risk details. "
            "Assume they know the basics."
        )
    else:
        persona = (
            "**ROLE:** You are speaking to a **Standard User**. "
            "Be friendly, helpful, and patient. Explain technical terms simply. "
            "Guide them step-by-step."
        )

    # 2. Detect Emotion
    emotion_context = detect_emotion(question)

    # 3. Invoke Chain
    try:
        response = rag_chain.invoke({
            "input": question, 
            "chat_history": chat_history,
            "persona": persona,
            "emotion_context": emotion_context
        })
        return response
    except Exception as e:
        print(f"RAG Invoke Error: {e}")
        return {"answer": "I encountered an error processing your request."}

def search_templates_with_rag(query):
    """
    Searches for templates using RAG (Semantic Search).
    """
    if not template_retriever:
        print("Template RAG not initialized.")
        return []
        
    try:
        docs = template_retriever.invoke(query)
        results = []
        for d in docs:
            # CSVLoader puts the row content in page_content. 
            # We need to parse it or rely on the fact that it's key: value format.
            # However, for structured data, it's better to extract fields if possible.
            # But CSVLoader combines all fields into text.
            
            # Let's try to parse the content back to dict if needed, 
            # or just extract what we need from the text if it's simple.
            # Actually, the 'metadata' usually contains 'row' index, but not the fields.
            # The page_content looks like:
            # template_number: ABC...
            # Name: ...
            
            content = d.page_content
            
            # Simple parsing of the content string to a dict
            row_data = {}
            for line in content.split('\n'):
                if ': ' in line:
                    key, val = line.split(': ', 1)
                    row_data[key.strip()] = val.strip()
            
            results.append({
                "sys_id": row_data.get('sys_id') or row_data.get('template_number', 'Unknown'),
                "name": row_data.get('Name', 'Unknown'),
                "short_description": row_data.get('Short_description', ''),
                "template": f"application={row_data.get('Application', '')}^implementation_plan={row_data.get('Implementation_plan', '')}",
                "source": "rag"
            })
            
        return results
    except Exception as e:
        print(f"Template RAG Search Error: {e}")
        return []

def analyze_risk_score(plan_text):
    if not llm or not retriever:
        return jsonify({"answer": "Risk analysis unavailable. System not initialized."})
    
    try:
        docs = retriever.invoke(plan_text)
        context_text = "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"Retrieval Error: {e}")
        context_text = "No specific SOPs found."

    prompt = (
        "You are a Change Management Risk Expert. Analyze the following implementation plan "
        "based on the provided context (SOPs) and standard risk assessment criteria.\n\n"
        f"Plan: {plan_text}\n\n"
        f"Context: {context_text}\n\n"
        "Provide a risk assessment in the following Markdown format:\n"
        "## Risk Assessment\n"
        "**Risk Score:** [High/Medium/Low]\n\n"
        "### Reasoning\n"
        "[Brief explanation]\n\n"
        "### Missing Mitigation Steps\n"
        "- [Step 1]\n"
        "- [Step 2]\n"
    )
    
    try:
        response = llm.invoke(prompt)
        return jsonify({"answer": response.content})
    except Exception as e:
        return jsonify({"answer": f"Error during risk analysis: {str(e)}"})

def translate_text(text, target_language):
    """
    Translates the given text to the target language using the LLM.
    Preserves formatting and placeholders.
    """
    if not llm:
        return text # Fallback if LLM not ready
        
    prompt = (
        f"Translate the following email draft into {target_language}. "
        "IMPORTANT RULES:\n"
        "1. Maintain the exact same structure and formatting (newlines, bullet points).\n"
        "2. DO NOT translate placeholders like [CR-ID], [Requester Name], [Manager Name], etc.\n"
        "3. DO NOT translate specific IDs like CR-123, CHG999.\n"
        "4. Keep the tone professional.\n\n"
        f"Text to translate:\n{text}"
    )
    
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Translation Error: {e}")
        return text # Fallback to original text on error

def contextualize_query(query, chat_history):
    """
    Reformulates the user's query based on chat history to make it standalone.
    Example: 
    History: "I need a template for DB" -> "Which DB?"
    Query: "Oracle"
    Result: "I need a template for Oracle DB"
    """
    if not llm or not chat_history:
        return query
        
    system_prompt = (
        "Given a chat history and the latest user response, "
        "reformulate the response into a standalone question or statement that includes the necessary context. "
        "If the user is answering a clarifying question, combine it with the previous context.\n"
        "Example:\n"
        "History: User='Template for DB', AI='Which DB?'\n"
        "Input: 'Oracle'\n"
        "Output: 'Template for Oracle DB'\n\n"
        "Output ONLY the reformulated question. Do NOT answer the question. Do NOT provide a list of templates."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    try:
        chain = prompt | llm
        response = chain.invoke({"input": query, "chat_history": chat_history})
        return response.content
    except Exception as e:
        print(f"Contextualization Error: {e}")
        return query

def classify_intent(query, chat_history=None):
    """
    Classifies the user's query into a specific intent using the LLM.
    """
    if not llm:
        return "GENERAL_QUERY" # Fallback
        
    # Contextualize if history exists
    if chat_history:
        query = contextualize_query(query, chat_history)
        print(f"DEBUG: Contextualized Query for Intent: {query}")
        
    system_prompt = (
        "You are an Intent Classifier for a Change Management Chatbot. "
        "Classify the user's query into EXACTLY ONE of the following categories:\n\n"
        
        "1. TICKET_STATUS: User wants to check the status or details of a specific ticket (e.g., 'Status of CR-123', 'Check CHG999').\n"
        "2. CREATE_CHANGE: User explicitly wants to create, raise, or draft a new change request (e.g., 'Create a change request', 'Raise a new ticket', 'Draft a change for...', 'Find similar changes for...').\n"
        "3. PENDING_APPROVALS: User asks about their pending approvals or approvals they need to action.\n"
        "4. PENDING_TASKS: User asks about their assigned tasks, work, or catalog tasks (e.g., 'Show my pending tasks', 'What tasks are assigned to me?', 'My tasks').\n"
        "5. DRAFT_EMAIL: User wants to draft an email, communication, or notification.\n"
        "6. RISK_ANALYSIS: User asks to analyze the risk of a plan or implementation steps.\n"
        "7. SCHEDULE_QUERY: User asks about the schedule, calendar, upcoming changes, planned maintenance, OR checks availability for a specific date (e.g., 'Can I schedule on Dec 25?', 'Is December 15 available?', 'Check conflicts for 2025-01-01').\n"
        "8. SHOW_STATS: User asks for charts, statistics, metrics, trends, or breakdowns.\n"
        "9. AUDIT_EMERGENCY: User wants to audit or analyze emergency changes for compliance.\n"
        "10. VALIDATE_EMERGENCY: User wants to validate if a change qualifies as emergency.\n"
        "11. TEMPLATE_LOOKUP: User is asking for a template, standard change, or recommendation for a specific activity, OR stating an intent to perform an activity without explicitly asking to create a ticket (e.g., 'template for oracle', 'standard change for patching', 'I need to patch my device', 'I am planning a deployment').\n"
        "    - RULE: If user says 'Create change...', classify as CREATE_CHANGE.\n"
        "    - RULE: If user says 'I need to [activity]' or 'Template for [activity]', classify as TEMPLATE_LOOKUP.\n"
        "12. GENERAL_QUERY: General questions, definitions, 'how-to' questions, greetings, or anything else.\n\n"
        
        "OUTPUT RULE: Return ONLY the category name (e.g., 'TICKET_STATUS'). Do not add any explanation."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    try:
        chain = prompt | llm
        response = chain.invoke({"input": query})
        intent = response.content.strip().upper()
        
        # Safety check to ensure valid intent
        valid_intents = [
            "TICKET_STATUS", "CREATE_CHANGE", "PENDING_APPROVALS", "PENDING_TASKS", 
            "DRAFT_EMAIL", "RISK_ANALYSIS", "SCHEDULE_QUERY", "SHOW_STATS", 
            "AUDIT_EMERGENCY", "VALIDATE_EMERGENCY", "TEMPLATE_LOOKUP", "GENERAL_QUERY"
        ]
        
        if intent not in valid_intents:
            # Fallback for hallucinated intents
            print(f"Warning: LLM returned invalid intent '{intent}'. Defaulting to GENERAL_QUERY.")
            return "GENERAL_QUERY"
            
        return intent
        
    except Exception as e:
        print(f"Intent Classification Error: {e}")
        return "GENERAL_QUERY"

def recommend_template(query, templates, keywords=None):
    """
    Uses LLM to recommend the best template from a list of options.
    """
    if not llm:
        return {"answer": "Template recommendation unavailable (LLM not ready)."}
        
    if not templates:
        return {"answer": "I couldn't find any relevant templates for your request."}

    # Fetch recent changes for reference
    # Fetch recent changes for reference
    recent_changes = []
    
    # Extract a specific search term from the query using LLM
    search_term = query
    try:
        if llm:
            extraction_prompt = (
                f"Analyze the user query: '{query}'\n"
                "Identify the single most relevant technical keyword or activity to search for similar Change Requests in ServiceNow.\n"
                "Examples:\n"
                "- 'I need to patch my device' -> 'patch'\n"
                "- 'Update the firewall rules' -> 'firewall'\n"
                "- 'Deploy new application' -> 'deploy'\n"
                "- 'Reboot the server' -> 'reboot'\n"
                "Return ONLY the keyword, nothing else."
            )
            search_term = llm.invoke(extraction_prompt).content.strip()
            # print(f"DEBUG: Extracted Search Term: {search_term}")
    except Exception as e:
        print(f"Keyword Extraction Error: {e}")

    if search_term:
        recent_changes = get_recent_changes_by_keyword(search_term, limit=10)
    
    reference_section_str = ""
    if recent_changes:
        reference_section_str = "Found these recent changes using similar templates:\n"
        for rc in recent_changes:
            reference_section_str += f"- {rc['number']}: {rc['short_description']}\n"

    # Format templates for the prompt
    template_list_str = ""
    INSTANCE = Config.SERVICENOW_INSTANCE
    
    import urllib.parse
    for i, t in enumerate(templates):
        sys_id = t.get('sys_id', '')
        # Encode the URI parameter to handle special characters and query strings correctly
        target_uri = f"sys_template.do?sys_id={sys_id}"
        encoded_uri = urllib.parse.quote(target_uri)
        link = f"{INSTANCE}/nav_to.do?uri={encoded_uri}"
        template_list_str += f"{i+1}. Name: {t.get('name')}\n   Description: {t.get('short_description')}\n   Fields: {t.get('template')}\n   Link: {link}\n\n"

    # Check if we are in fallback mode (Only generic template found)
    is_fallback = False
    if len(templates) == 1 and "ABC00000" in templates[0].get('name', ''):
        is_fallback = True

    prompt = (
        "You are a Change Management Assistant. The user asked for a template.\n"
        "I have found the following templates in ServiceNow:\n\n"
        f"{template_list_str}\n"
        f"User Query: \"{query}\"\n"
        f"Recent Reference Changes:\n{reference_section_str}\n\n"
        "Task:\n"
        "1. Analyze the user's intent and the available templates.\n"
        "2. **CLARIFICATION CHECK**: \n"
        "   - Analyze the found templates. Do they cover multiple **distinct** options (e.g., different Databases, OS versions, Applications, or specific Activities)?\n"
        "   - Analyze the User Query. Did the user specify the exact type/option they need?\n"
    )
    prompt += (
        "   - **CRITICAL RULE**: If the user's query is broad (e.g., 'patch my device', 'update server', 'fix database') and matches multiple different types of templates (e.g., Windows vs Linux, Oracle vs SQL), you **MUST** ask a clarifying question.\n"
        "   - **DO NOT** list templates if the query is ambiguous. Ask the question instead.\n"
        "   - **INTERACTIVE OPTIONS**: Along with the question, provide clickable buttons for **ALL** distinct options found. **Do not limit the number of buttons.** If there are 10 distinct options, show 10 buttons. **These options MUST be derived from the templates you found.**\n"
        "   - **Instruction Text**: Before the buttons, add this exact sentence followed by a line break: \"Here are some suggestions, please click a button below to proceed:<br>\"\n"
        "   - **Button Format**: Use the following HTML format for each option. **DO NOT use markdown bullets or lists for these options.** Output the raw HTML directly.\n"
        "     `<button onclick=\"document.getElementById('user-input').value='[Option Text]'; document.getElementById('user-input').focus();\" style='background-color: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; margin-right: 8px; margin-top: 8px; transition: all 0.2s; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);'>[Option Text]</button>`\n"
        "   - **Example Output**:\n"
        "     Which device would you like to patch?\n"
        "     Here are some suggestions, please click a button below to proceed:\n"
        "     <button ...>Windows Server</button> <button ...>Linux Server</button>\n"
        "   - **Output**: Return the clarifying question, followed by the instruction text, followed by the HTML buttons.\n"
        "3. If no clarification is needed (or user already specified), list ALL relevant templates found (up to 10).\n"
        "4. If listing templates, format them EXACTLY as follows:\n"
    )

    if is_fallback:
        prompt += (
            "   - **IMPORTANT**: Since only the generic template (ABC00000) was found, you MUST start your response by explicitly stating:\n"
            "   \"I couldn't find any specific matching templates for your request, so I suggest using the generic template below.\"\n"
        )

    prompt += (
        "   - **Template Name** (Header) [HTML Button to View in ServiceNow]\n"
        "   - **Description**: [One line description]\n"
        "   - **Pre-filled Fields**: [List each field on a new line with a bullet point]\n"
        "   - **Few change references raised recently using this template**:\n"
        "     > [Change Number] - [Short Description] [HTML Button to Clone]\n"
        "     (Select up to 2 relevant changes from the 'Recent Reference Changes' list above. If none are relevant, say 'No recent change references found'.)\n\n"
        "Output Format:\n"
    )
    
    if is_fallback:
        prompt += "I couldn't find any specific matching templates for your request, so I suggest using the generic template below:\n\n"

    prompt += (
        "### 1. [Template Name] <a href='[Link]' target='_blank' style='background-color: #293e40; color: white; padding: 5px 10px; text-decoration: none; border-radius: 5px; font-size: 12px; vertical-align: middle; margin-left: 10px;'>🔗 View in ServiceNow</a>\n\n"
        "**Description**: [Description]\n\n"
        "**Pre-filled Fields**:\n"
        "- **Field Name**: Value\n"
        "- **Field Name**: Value\n\n"
        "**Few change references raised recently using this template**:\n"
        "<div style='background: #f8f9fa; border-left: 3px solid #6366f1; border-radius: 4px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>"
        "  <div style='display: flex; flex-direction: column;'>"
        "    <span style='font-weight: 600; color: #2c3e50; font-size: 13px;'>[Change Number]</span>"
        "    <span style='color: #6c757d; font-size: 12px; margin-top: 2px;'>[Short Description]</span>"
        "  </div>"
        "  <div style='display: flex; flex-direction: column; gap: 5px;'>"
        "    <button onclick=\"document.getElementById('user-input').value='Clone [Change Number]'; document.getElementById('chat-form').requestSubmit();\" style='background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2); white-space: nowrap;'>Clone This</button>"
        "    <button onclick=\"document.getElementById('user-input').value='Check [Change Number]'; document.getElementById('chat-form').requestSubmit();\" style='background: #6c757d; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); white-space: nowrap;'>View Change</button>"
        "  </div>"
        "</div>\n"
        "<div style='background: #f8f9fa; border-left: 3px solid #6366f1; border-radius: 4px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>"
        "  <div style='display: flex; flex-direction: column;'>"
        "    <span style='font-weight: 600; color: #2c3e50; font-size: 13px;'>[Change Number]</span>"
        "    <span style='color: #6c757d; font-size: 12px; margin-top: 2px;'>[Short Description]</span>"
        "  </div>"
        "  <div style='display: flex; flex-direction: column; gap: 5px;'>"
        "    <button onclick=\"document.getElementById('user-input').value='Clone [Change Number]'; document.getElementById('chat-form').requestSubmit();\" style='background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2); white-space: nowrap;'>Clone This</button>"
        "    <button onclick=\"document.getElementById('user-input').value='Check [Change Number]'; document.getElementById('chat-form').requestSubmit();\" style='background: #6c757d; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); white-space: nowrap;'>View Change</button>"
        "  </div>"
        "</div>\n"
    )
    
    if not is_fallback:
        prompt += (
            "### 2. [Template Name]\n"
            "...\n"
        )
    
    try:
        response = llm.invoke(prompt)
        return {"answer": response.content}
    except Exception as e:
        print(f"Template Recommendation Error: {e}")
        return {"answer": "I encountered an error analyzing the templates."}

def extract_template_keywords(query):
    """
    Uses LLM to extract specific search keywords for ServiceNow templates from a natural language query.
    Example: "move to cloud" -> "Cloud Scaling"
    """
    if not llm:
        return query # Fallback

    prompt = (
        "You are a helper for a ServiceNow search engine.\n"
        "Extract 1-2 specific, high-value keywords from the user's query to search for a Standard Change Template.\n"
        "Focus on the technical activity (e.g., 'Firewall', 'Oracle', 'Patch', 'Reboot', 'Cloud').\n"
        "Do not include generic words like 'create', 'change', 'ticket', 'template', 'request'.\n\n"
        f"User Query: \"{query}\"\n\n"
        "Output ONLY the keywords separated by space. Do not add quotes or labels."
    )
    
    try:
        response = llm.invoke(prompt)
        keywords = response.content.strip()
        print(f"DEBUG: Extracted Keywords: {keywords}")
        return keywords
    except Exception as e:
        print(f"Keyword Extraction Error: {e}")
        return query
