import streamlit as st
import httpx
import json

# 1. Page Configuration
st.set_page_config(page_title="Smart LLM Router", page_icon="🤖", layout="centered")
st.title("🤖 Smart LLM Router")
st.caption("Local AI Gateway & Intelligent Router powered by FastAPI + Ollama")

# 2. Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Capture User Input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Append to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Render Assistant Response Container
    with st.chat_message("assistant"):
        placeholder = st.empty()  # Dynamic container for streaming text
        full_response = ""
        
        # Payload aligned with your FastAPI gateway contract
        payload = {
            "model": "deepseek-r1:8b",
            "messages": st.session_state.messages,
            "stream": True
        }
        
        try:
            # 5. Stream request to your FastAPI gateway (Port 8000)
            with httpx.stream("POST", "http://127.0.0.1:8000/v1/chat/completions", json=payload, timeout=None) as r:
                if r.status_code != 200:
                    st.error(f"Gateway Error. Status Code: {r.status_code}")
                
                # 6. Parse Server-Sent Events (SSE) Stream Line by Line
                for line in r.iter_lines():
                    if not line:
                        continue
                    
                    # Check standard SSE prefix
                    if line.startswith("data: "):
                        data_content = line[6:]
                        
                        # Check end flag
                        if data_content.strip() == "[DONE]":
                            break
                        
                        try:
                            # Parse Chunk JSON
                            chunk_json = json.loads(data_content)
                            delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                            
                            # Extract incremental text token
                            if "content" in delta:
                                full_response += delta["content"]
                                # Update UI with a typing cursor indicator
                                placeholder.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            pass
            
            # Streaming finished, render final text block
            placeholder.markdown(full_response)
            # Append complete response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except httpx.ConnectError:
            st.error("Failed to connect to the gateway! Please ensure your FastAPI server is running on Port 8000.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            
            