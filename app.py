"""
Streamlit Frontend with Authentication & File Upload
"""
import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import chatbot
from memory import get_all_threads, get_conversation_title, store_memory
from auth import auth
from document_analyzer import doc_analyzer, ask_document
from voiceinput import voice_input

# ============ Page Config ============
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# ============ Helper Functions ============
def new_thread_id():
    """Create new conversation ID"""
    return str(uuid.uuid4())


def reset_chat():
    """Start new chat"""
    st.session_state['thread_id'] = new_thread_id()
    st.session_state['message_history'] = []
    st.rerun()


def load_conversation(thread_id):
    """Load old conversation"""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    messages = state.values.get('messages', None)
    if not messages:
        return None
    return messages


def get_user_threads(user_id):
    """Get threads for specific user only"""
    all_threads = get_all_threads()
    # Filter threads by user_id (stored in thread metadata)
    user_threads = [t for t in all_threads if str(user_id) in str(t)]
    return user_threads


# ============ Authentication Pages ============
def show_login_page():
    """Display login form"""
    st.title("🔐 Login to AI Assistant")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            with col_b:
                signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
            
            if login_btn:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    result = auth.login_user(username, password)
                    if result["success"]:
                        st.session_state["session_id"] = result["session_id"]
                        st.session_state["user_id"] = result["user_id"]
                        st.session_state["username"] = result["username"]
                        st.session_state["subscription_tier"] = result["subscription_tier"]
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["error"])
            
            if signup_btn:
                st.session_state["show_signup"] = True
                st.rerun()


def show_signup_page():
    """Display signup form"""
    st.title("📝 Create Your Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Choose a username (min 3 chars)")
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 chars)")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                signup_btn = st.form_submit_button("✅ Create Account", use_container_width=True)
            with col_b:
                back_btn = st.form_submit_button("← Back to Login", use_container_width=True)
            
            if signup_btn:
                if not all([username, email, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    result = auth.register_user(username, email, password)
                    if result["success"]:
                        st.success(result["message"])
                        st.info("Please login with your credentials")
                        st.session_state["show_signup"] = False
                        st.rerun()
                    else:
                        st.error(result["error"])
            
            if back_btn:
                st.session_state["show_signup"] = False
                st.rerun()


# ============ Check Authentication ============
if "session_id" not in st.session_state:
    # User not logged in
    if st.session_state.get("show_signup", False):
        show_signup_page()
    else:
        show_login_page()
    st.stop()

# Verify session
session_info = auth.verify_session(st.session_state["session_id"])
if not session_info.get("valid"):
    st.error("Session expired. Please login again.")
    del st.session_state["session_id"]
    st.rerun()

# Update user info from session
st.session_state["user_id"] = session_info["user_id"]
st.session_state["username"] = session_info["username"]
st.session_state["subscription_tier"] = session_info["subscription_tier"]


# ============ Initialize Session ============
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = get_user_threads(st.session_state["user_id"])

if 'thread_id' not in st.session_state:
    all_threads = st.session_state['chat_threads']
    if all_threads:
        st.session_state['thread_id'] = all_threads[-1]
    else:
        st.session_state['thread_id'] = f"{st.session_state['user_id']}_{new_thread_id()}"

if 'message_history' not in st.session_state:
    messages = load_conversation(st.session_state['thread_id'])
    if messages:
        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages
    else:
        st.session_state['message_history'] = []


# ============ Sidebar ============
with st.sidebar:
    st.title('🤖 AI Assistant')
    
    # User info
    st.markdown(f"👤 **{st.session_state['username']}**")
    tier_emoji = "⭐" if st.session_state['subscription_tier'] == 'pro' else "🆓"
    st.caption(f"{tier_emoji} {st.session_state['subscription_tier'].upper()} Plan")
    
    st.divider()
    
    # New Chat button
    if st.button('➕ New Chat', use_container_width=True):
        reset_chat()
    
    # File Upload Section
    st.subheader('📄 Upload Document')
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, or TXT",
        type=['pdf', 'docx', 'txt'],
        help="Upload documents to ask questions about them"
    )
    
    if uploaded_file:
        with st.spinner('Processing document...'):
            result = doc_analyzer.upload_document(uploaded_file, st.session_state["user_id"])
            if result["success"]:
                st.success(result["message"])
                st.info(f"📊 {result['chunks']} chunks indexed")
            else:
                st.error(result["error"])
    
    # Show uploaded documents
    user_docs = doc_analyzer.get_user_documents(st.session_state["user_id"])
    if user_docs:
        with st.expander(f"📚 My Documents ({len(user_docs)})"):
            for doc in user_docs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {doc['filename'][:25]}...")
                with col2:
                    if st.button("🗑️", key=f"del_doc_{doc['document_id']}"):
                        doc_analyzer.delete_document(st.session_state["user_id"], doc['document_id'])
                        st.rerun()
    
    st.divider()
    
    # Conversations
    st.subheader('💬 My Chats')
    for thread_id in st.session_state['chat_threads'][::-1]:
        title = get_conversation_title(thread_id)
        if st.button(title, key=str(thread_id), use_container_width=True):
            messages = load_conversation(thread_id)
            if messages:
                st.session_state['thread_id'] = thread_id
                temp_messages = []
                for msg in messages:
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    temp_messages.append({'role': role, 'content': msg.content})
                st.session_state['message_history'] = temp_messages
                st.rerun()
    
    st.divider()
    
    # Export Chat
    if st.button("📥 Export Chat", use_container_width=True):
        messages = st.session_state.get('message_history', [])
        export_text = f"# Chat Export\n\n**User:** {st.session_state['username']}\n\n---\n\n"
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            export_text += f"**{role}:**\n{content}\n\n"
        
        st.download_button(
            label="💾 Download Markdown",
            data=export_text,
            file_name=f"chat_{st.session_state['thread_id'][:8]}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    st.divider()
    
    # Session Stats
    st.subheader("📊 Stats")
    import tiktoken
    def count_tokens(text):
        encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        return len(encoding.encode(text))
    
    total_tokens = sum(
        count_tokens(msg['content']) 
        for msg in st.session_state.get('message_history', [])
    )
    
    col1, col2 = st.columns(2)
    col1.metric("Messages", len(st.session_state.get('message_history', [])))
    col2.metric("Tokens", total_tokens)
    
    cost = (total_tokens / 1000) * 0.00015
    st.caption(f"💰 Cost: ${cost:.4f}")
    
    st.divider()
    
    # Logout
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout_user(st.session_state["session_id"])
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ============ Chat Display ============
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


# ============ Chat Input ============

"""
Fixed Voice Input Section for frontend.py
Replace your current voice input section with this
"""

# ============ Voice Input Section (FIXED) ============
from voiceinput import voice_input

# Initialize processed audio tracker
if 'processed_audio_id' not in st.session_state:
    st.session_state['processed_audio_id'] = None

# Voice Input UI
col1, col2 = st.columns([4, 1])

with col2:
    voice_option = st.selectbox(
        "🎤 Input",
        ["Type", "Voice"],
        label_visibility="collapsed"
    )

# Show voice input if selected
if voice_option == "Voice":
    st.info("🎤 Record your message using the audio input below")
    
    # Streamlit's native audio input
    audio_file = st.audio_input("Record your question")
    
    if audio_file:
        # Create unique ID for this audio file
        import hashlib
        audio_id = hashlib.md5(audio_file.getvalue()).hexdigest()
        
        # Only process if we haven't processed this exact audio before
        if audio_id != st.session_state.get('processed_audio_id'):
            with st.spinner("🎧 Transcribing audio..."):
                result = voice_input.transcribe_audio_file(audio_file)
                
                if result["success"]:
                    st.success(f"✅ Transcribed: {result['text']}")
                    
                    # Mark this audio as processed
                    st.session_state['processed_audio_id'] = audio_id
                    
                    # Store the transcribed text
                    user_input = result['text']
                    
                    # Process the voice input
                    st.session_state["message_history"].append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    with st.chat_message("user"):
                        st.markdown(user_input)
                    
                    # Store user message in memory
                    from memory import store_memory
                    store_memory(st.session_state["thread_id"], user_input, "user")
                    
                    # Config
                    CONFIG = {
                        "configurable": {
                            "thread_id": st.session_state["thread_id"],
                            "user_id": st.session_state["user_id"]
                        },
                        "metadata": {"thread_id": st.session_state["thread_id"]},
                        "run_name": "chat_turn",
                    }
                    
                    # Get AI response
                    with st.chat_message("assistant"):
                        status_box = {"box": None}
                        
                        def ai_stream():
                            for msg_chunk, metadata in chatbot.stream(
                                {"messages": [HumanMessage(content=user_input)]},
                                config=CONFIG,
                                stream_mode="messages",
                            ):
                                if isinstance(msg_chunk, ToolMessage):
                                    tool_name = getattr(msg_chunk, "name", "tool")
                                    if status_box["box"] is None:
                                        status_box["box"] = st.status(
                                            f"🔧 Using `{tool_name}` …",
                                            expanded=True
                                        )
                                    else:
                                        status_box["box"].update(
                                            label=f"🔧 Using `{tool_name}` …",
                                            state="running"
                                        )
                                
                                if isinstance(msg_chunk, AIMessage):
                                    yield msg_chunk.content
                        
                        ai_message = st.write_stream(ai_stream())
                        
                        if status_box["box"]:
                            status_box["box"].update(
                                label="✅ Tool finished",
                                state="complete",
                                expanded=False
                            )
                    
                    # Save response
                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    # Store assistant response in memory
                    store_memory(st.session_state["thread_id"], ai_message, "assistant")
                    
                    # Clear the processed audio ID after successful processing
                    # This allows recording new audio
                    st.session_state['processed_audio_id'] = None
                    
                    # Rerun to show updated chat
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
        else:
            # Audio already processed, show info
            st.info("✅ Audio already processed. Record a new message to continue.")


# ============ Chat Input (Keep as is) ============
if voice_option == "Type":
    user_input = st.chat_input('💭 Type your message...')
    
    if user_input:
        # Your existing chat input code
        st.session_state["message_history"].append({
            "role": "user",
            "content": user_input
        })
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Store user message in memory
        from memory import store_memory
        store_memory(st.session_state["thread_id"], user_input, "user")
        
        # Config
        CONFIG = {
            "configurable": {
                "thread_id": st.session_state["thread_id"],
                "user_id": st.session_state["user_id"]
            },
            "metadata": {"thread_id": st.session_state["thread_id"]},
            "run_name": "chat_turn",
        }
        
        # Get AI response
        with st.chat_message("assistant"):
            status_box = {"box": None}
            
            def ai_stream():
                for msg_chunk, metadata in chatbot.stream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode="messages",
                ):
                    if isinstance(msg_chunk, ToolMessage):
                        tool_name = getattr(msg_chunk, "name", "tool")
                        if status_box["box"] is None:
                            status_box["box"] = st.status(
                                f"🔧 Using `{tool_name}` …",
                                expanded=True
                            )
                        else:
                            status_box["box"].update(
                                label=f"🔧 Using `{tool_name}` …",
                                state="running"
                            )
                    
                    if isinstance(msg_chunk, AIMessage):
                        yield msg_chunk.content
            
            ai_message = st.write_stream(ai_stream())
            
            if status_box["box"]:
                status_box["box"].update(
                    label="✅ Tool finished",
                    state="complete",
                    expanded=False
                )
        
        # Save response
        st.session_state["message_history"].append({
            "role": "assistant",
            "content": ai_message
        })
        
        # Store assistant response in memory
        store_memory(st.session_state["thread_id"], ai_message, "assistant")