import os
from flask import jsonify
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config import Config

# Global State
rag_chain = None
llm = None
retriever = None

def initialize_rag_chain():
    global rag_chain, llm, retriever
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
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, convert_system_message_to_human=True)

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
