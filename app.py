import streamlit as st
import requests

# Configuration (will use Streamlit secrets)
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "8abe74e8-b551-40dd-967c-3c17342f6ee1"
FLOW_ID = "c9ba954e-3449-4d12-9a07-eec02d8c591f"

# Pre-configured tweaks (modify if needed)
TWEAKS = {
    "ChatInput-EnnWC": {},
    "ParseData-4Mivh": {},
    "Prompt-qPeMa": {},
    "ChatOutput-mEMTU": {},
    "OpenAIEmbeddings-pxjJu": {},
    "OpenAIModel-YpfiT": {},
    "AstraDB-jOu2s": {}
}

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Streamlit UI
st.set_page_config(page_title="Astra DB Chat", page_icon="🤖")
st.title("Enterprise Knowledge Assistant")

def get_response(prompt: str) -> str:
    """Get response from Langflow API"""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{FLOW_ID}"
    
    payload = {
        "input_value": prompt,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS
    }
    
    headers = {
        "Authorization": f"Bearer {st.secrets['APPLICATION_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        return response.json().get("result", "No response received")
    except Exception as e:
        return f"API Error: {str(e)}"

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your enterprise data"):
    # Add user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response
    with st.spinner("Analyzing knowledge base..."):
        response = get_response(prompt)
    
    # Add assistant response
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
