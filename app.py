import streamlit as st
import json
import requests
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up a session with retries and longer timeouts
def create_requests_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# Constants
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "8abe74e8-b551-40dd-967c-3c17342f6ee1"
FLOW_ID = "c9ba954e-3449-4d12-9a07-eec02d8c591f"

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
    if tweaks:
        payload["tweaks"] = tweaks

    headers = {
        "Content-Type": "application/json"
    }
    if application_token:
        headers["Authorization"] = f"Bearer {application_token}"

    session = create_requests_session()
    
    try:
        with st.spinner("Waiting for response from Langflow (this might take a while)..."):
            # Increased timeout to 180 seconds (3 minutes)
            response = session.post(
                api_url, 
                json=payload, 
                headers=headers,
                timeout=180  # Extended timeout
            )
            response.raise_for_status()
            return response.json()
    except requests.exceptions.Timeout:
        st.error("The request timed out. Langflow is taking longer than usual to respond. Please try again.")
        return {"error": "Request timed out"}
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
        response = run_flow(
            message=prompt,
            endpoint=FLOW_ID,
            tweaks=None,
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
                response.get("response") or
                response.get("output") or
                response.get("result") or
                (response.get("data", {}).get("result") if isinstance(response.get("data"), dict) else None) or
                str(response)
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
    st.markdown("### Note")
    st.markdown("Responses might take up to 3 minutes during high load times.")
