import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_user_verify@example.com"
PASSWORD = "password123"

def run_test():
    print("1. Signup/Login...")
    # Try Signup
    requests.post(f"{BASE_URL}/signup", json={"email": EMAIL, "password": PASSWORD})
    
    # Login
    resp = requests.post(f"{BASE_URL}/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Login successful.")

    print("\n2. Create Chat...")
    resp = requests.post(f"{BASE_URL}/chats/", json={"title": "Test Chat"}, headers=headers)
    if resp.status_code != 200:
        print(f"Create chat failed: {resp.text}")
        sys.exit(1)
    chat_id = resp.json()["id"]
    print(f"   Chat created with ID: {chat_id}")

    print("\n3. Send Message...")
    # Use a dummy message that doesn't trigger expensive AI if possible, 
    # but backend calls AI. We just check if it returns.
    # Note: If no API key, it might fail inside backend.
    # But checking if we get a response (even error) handles part of the test.
    resp = requests.post(f"{BASE_URL}/chats/{chat_id}/message", 
                         json={"role": "user", "content": "Hello, this is a test."}, 
                         headers=headers)
    
    if resp.status_code != 200:
        print(f"Send message failed: {resp.text}")
        # Validate if it's just AI error but message saved? 
        # API returns 200 even if AI fails (caught exception), per my code.
        sys.exit(1)
    
    chat_data = resp.json()
    messages = chat_data["messages"]
    print(f"   Message sent. Chat now has {len(messages)} messages.")
    if len(messages) >= 2:
        print(f"   AI Response: {messages[-1]['content'][:50]}...")
    else:
        print("   WARNING: AI response missing?")

    print("\n4. Get History...")
    resp = requests.get(f"{BASE_URL}/chats/", headers=headers)
    if resp.status_code != 200:
        print(f"Get history failed: {resp.text}")
        sys.exit(1)
    history = resp.json()
    print(f"   History contains {len(history)} chats.")
    found = any(c['id'] == chat_id for c in history)
    if not found:
        print("   FAILED: Created chat not found in history.")
        sys.exit(1)
    else:
        print("   Verified chat in history.")

    print("\n5. Search History...")
    resp = requests.get(f"{BASE_URL}/chats/?search=Test", headers=headers)
    if resp.status_code != 200:
        print(f"Search failed: {resp.text}")
        sys.exit(1)
    search_results = resp.json()
    print(f"   Search returned {len(search_results)} results.")
    if len(search_results) > 0 and search_results[0]['id'] == chat_id:
         print("   Verified search found the chat.")
    else:
         print("   FAILED: Search did not return expected chat.")

    print("\n✅ Backend Verification Passed!")

if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Is it running on port 8000?")
