import os
from dotenv import load_dotenv
import streamlit as st
import requests
import json

# Load environment variables
load_dotenv()

# Environment Variables
JAMAI_API_KEY = os.getenv("JAMAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
BASE_URL = os.getenv("BASE_URL")
TASK_TABLE_ID = os.getenv("TASK_TABLE_ID")
PRODUCTIVITY_TIPS_TABLE_ID = os.getenv("PRODUCTIVITY_TIPS_TABLE_ID")
CHAT_COMPLETIONS_ENDPOINT = f"{BASE_URL}/api/v1/chat/completions"
KNOWLEDGE_TABLE_ID = os.getenv("productivity_ideas")
CHAT_TABLE_ID = os.getenv("CHAT_TABLE_ID")

# API Headers
headers = {
    "Authorization": f"Bearer {JAMAI_API_KEY}",
    "X-PROJECT-ID": PROJECT_ID,
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# Function to add user inputs and AI responses to the Chat Table
def add_response_to_chat_table(user_input, ai_response):
    url = f"{BASE_URL}/api/v1/gen_tables/chat/rows/add"
    payload = {
        "table_id": CHAT_TABLE_ID,
        "data": [
            {
                "User": user_input,
                "AI": ai_response
            }
        ]
    }

    # Debugging Payload
    print("Payload being sent to Chat Table:", json.dumps(payload, indent=2))

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        st.success("Response logged successfully!")
    else:
        st.error(f"Error adding response to chat table: {response.text}")


# Function to fetch a response from the Knowledge Table using RAG
def get_chat_response_from_knowledge_table(user_input):
    payload = {
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "model": "ellm/meta-llama/Llama-3.1-8B-Instruct",
        "knowledge_table_id": KNOWLEDGE_TABLE_ID,
        "temperature": 0.7,
        "max_tokens": 200,
        "reranking_model": "cohere/embed-multilingual-v3.0",
        "k": 3,
        "stream": True
    }

    response = requests.post(CHAT_COMPLETIONS_ENDPOINT, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        full_response = ""
        for chunk in response.iter_lines():
            if chunk:
                chunk_data = chunk.decode("utf-8")
                if chunk_data.startswith("data: "):
                    chunk_data = chunk_data[6:]
                    if chunk_data.strip() == "[DONE]":
                        break
                    try:
                        json_data = json.loads(chunk_data)
                        if "choices" in json_data and json_data["choices"]:
                            content = json_data["choices"][0]["delta"].get("content", "")
                            full_response += content
                    except json.JSONDecodeError:
                        continue
        return full_response.strip()
    else:
        st.error(f"Error fetching response: {response.status_code} - {response.text}")
        return "I couldn't find an answer. Please try rephrasing your query."


# Streamlit Page Configuration
st.set_page_config(page_title="ScheduleAI", page_icon="🤖", layout="wide")
st.title("🤖 ScheduleBot Chatbot")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Chat History

for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['user_input']}")
    st.markdown(f"**AI:** {chat['ai_response']}")

# Bottom-aligned Input Box and Send Button
st.markdown("---")
st.markdown("### Ask a Question")
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

user_input = st.text_input("Chat Input", value=st.session_state.input_text, placeholder="Type your message here...",
                           key="user_input", label_visibility="collapsed")
send_button = st.button("Send", use_container_width=True)


# Handle User Input
if send_button and user_input:
    # Fetch AI response
    ai_response = get_chat_response_from_knowledge_table(user_input)

    # Add to chat history
    st.session_state.chat_history.append({"user_input": user_input, "ai_response": ai_response})

    # Display the latest AI response in the "Ask a Question" section
    st.markdown(f"**AI:** {ai_response}")

    # Log response in the chat table
    add_response_to_chat_table(user_input, ai_response)

    # Clear the input box after submission
    st.session_state.input_text = ""
