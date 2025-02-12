import streamlit as st
import json
import requests
from typing import Optional

# Constants from your Langflow setup
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "8abe74e8-b551-40dd-967c-3c17342f6ee1"
FLOW_ID = "c9ba954e-3449-4d12-9a07-eec02d8c591f"
TWEAKS = {
    "ChatInput-EnnWC": {},
    "ParseData-4Mivh": {},
    "Prompt-qPeMa": {},
    "ChatOutput-mEMTU": {},
    "OpenAIEmbeddings-pxjJu": {},
    "OpenAIModel-YpfiT": {},
    "AstraDB-jOu2s": {}
}

def run_flow(
    message: str,
    endpoint: str,
    output_type: str = "chat",
    input_type: str = "chat",
    tweaks: Optional[dict] = None,
    application_token: Optional[str] = None
) -> dict:
    """Run a flow with a given message and optional tweaks."""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"

    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    if tweaks:
        payload["tweaks"] = tweaks
    if application_token:
        headers = {"Authorization": "Bearer " + application_token, "Content-Type": "application/json"}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with Langflow: {str(e)}")
        return {"error": str(e)}

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Streamlit app configuration
st.set_page_config(page_title="PLC Chatbot", page_icon="🤖")
st.title("PLC Chatbot")

# Add a debug expander
with st.expander("Debug Information"):
    st.write("This section shows raw API responses for debugging")
    if "last_response" in st.session_state:
        st.json(st.session_state.last_response)

# Chat interface
for message in st.session_state.messages:
    role = "assistant" if message["role"] == "assistant" else "user"
    with st.chat_message(role):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask something about PLCs..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_flow(
                message=prompt,
                endpoint=FLOW_ID,
                tweaks=TWEAKS,
                application_token=st.secrets["APPLICATION_TOKEN"]
            )
            
            # Store raw response for debugging
            st.session_state.last_response = response
            
            # Extract the actual response text from the Langflow response
            if "error" in response:
                response_text = f"Error: {response['error']}"
            else:
                # Try different possible response structures
                response_text = (
                    response.get("response") or  # Try direct response
                    response.get("output") or    # Try output field
                    response.get("result") or    # Try result field
                    (response.get("data", {}).get("result") if isinstance(response.get("data"), dict) else None) or  # Try nested data.result
                    str(response)  # Fallback to string representation
                )
            
            st.markdown(response_text)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Add sidebar with information
with st.sidebar:
    st.markdown("### About")
    st.markdown("This chatbot helps answer questions about PLCs.")
    st.markdown("### Instructions")
    st.markdown("Simply type your question in the chat box below and press Enter.")
