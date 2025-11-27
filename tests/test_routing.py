import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def login():
    print("Logging in...")
    response = SESSION.post(f"{BASE_URL}/login", data={
        "username": "user",
        "password": "password",
        "role": "User"
    })
    if response.status_code == 200:
        print("✅ Login Successful")
    else:
        print(f"❌ Login Failed: {response.status_code}")

def test_query(query, expected_intent_hint=None):
    print(f"\n--- Testing Query: '{query}' ---")
    try:
        response = SESSION.post(f"{BASE_URL}/ask", json={"question": query, "chat_history": []})
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            print(f"Response Status: 200 OK")
            print(f"Answer Preview: {answer[:100]}...")
            
            # Heuristic checks
            if expected_intent_hint == "SCHEDULE":
                if "table" in answer or "changes" in answer.lower():
                    print("✅ PASS: Looks like a Schedule/Table response.")
                else:
                    print("❌ FAIL: Expected Schedule/Table response.")
            elif expected_intent_hint == "GENERAL":
                if "table" not in answer and "changes" not in answer.lower(): # Rough check
                     print("✅ PASS: Looks like a General/RAG response.")
                else:
                     print("⚠️ WARN: Might be a false positive schedule response.")
            
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    # Wait for server to potentially reload
    print("Waiting for server to reload...")
    time.sleep(5)
    
    login()
    
    # 1. The original failure case
    test_query("Explain the difference between standard and normal changes", expected_intent_hint="GENERAL")
    
    # 2. The valid schedule case
    test_query("Show me upcoming changes", expected_intent_hint="SCHEDULE")
    
    # 3. Ambiguous case (should be schedule now if LLM is smart, or General)
    test_query("changes today", expected_intent_hint="SCHEDULE")
    
    # 4. Ticket status (CR-1024 exists in mock DB)
    test_query("Status of CR-1024", expected_intent_hint="TICKET")
    
    # 5. Email draft
    test_query("Draft an email about the server outage")

    # 6. Smart Change Creator (Suggestion)
    test_query("I need to upgrade the database", expected_intent_hint="CREATE")
    
    # 7. Smart Change Creator (Cloning)
    test_query("Clone CR-1024 for 2025-12-01 to 2025-12-02", expected_intent_hint="CREATE")

    # 8. Smart Change Creator (Cloning with Assignee)
    test_query("Clone CR-1024 for 2025-12-01 to 2025-12-02 assigned to Bob Smith", expected_intent_hint="CREATE")
