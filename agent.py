"""
Agent and graph setup
"""
from typing import Annotated, TypedDict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import config
import memory
import tools


# ============ State Definition ============
class ChatState(TypedDict):
    """What data flows through the graph"""
    messages: Annotated[list[BaseMessage], add_messages]


# ============ LLM Setup ============
llm = ChatOpenAI(
    model=config.LLM_MODEL,
    openai_api_key=config.OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    max_tokens=config.MAX_TOKENS
)

llm_with_tools = llm.bind_tools(tools.all_tools)


# ============ Agent Node ============


"""
Add this to your agent.py to fix token limit issues
"""
import tiktoken

def count_tokens(messages):
    """Count tokens in message list"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        total_tokens = 0
        for msg in messages:
            # Count message content
            if hasattr(msg, 'content'):
                total_tokens += len(encoding.encode(str(msg.content)))
            # Add overhead for message formatting (~4 tokens per message)
            total_tokens += 4
        return total_tokens
    except Exception:
        # Fallback: rough estimate (4 chars = 1 token)
        return sum(len(str(msg.content)) for msg in messages if hasattr(msg, 'content')) // 4


def truncate_messages(messages, max_tokens=10000):
    """
    Truncate old messages to stay within token limit
    Keep system message, recent messages, and important context
    """
    if not messages:
        return messages
    
    # Always keep system message if it exists
    system_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'system']
    other_messages = [msg for msg in messages if msg not in system_messages]
    
    # Count current tokens
    current_tokens = count_tokens(messages)
    
    if current_tokens <= max_tokens:
        return messages
    
    # Keep recent messages (last 10 exchanges = 20 messages)
    recent_count = min(20, len(other_messages))
    recent_messages = other_messages[-recent_count:]
    
    # Check if recent messages fit
    truncated = system_messages + recent_messages
    truncated_tokens = count_tokens(truncated)
    
    if truncated_tokens <= max_tokens:
        return truncated
    
    # If still too many, reduce further
    while truncated_tokens > max_tokens and len(recent_messages) > 4:
        recent_messages = recent_messages[-len(recent_messages)//2:]
        truncated = system_messages + recent_messages
        truncated_tokens = count_tokens(truncated)
    
    return truncated


# Update your chat_node function in agent.py:
def chat_node(state: ChatState, config: Any):
    """Main chat processing node with token management"""
    messages = state.get("messages", [])
    thread_id = config['configurable'].get('thread_id')
    
    # Get the last user message
    user_message = messages[-1].content if messages else ""
    
    # CRITICAL FIX: Truncate messages to avoid token limit
    messages = truncate_messages(messages, max_tokens=10000)
    
    # Try to retrieve relevant memories
    try:
        relevant_memories = memory.retrieve_memory(thread_id, user_message, limit=3)
        
        if relevant_memories:
            context = "\n".join([f"- {mem}" for mem in relevant_memories])
            context_message = f"\n\nRelevant context from earlier:\n{context}"
            
            # Add context to the last message
            enriched_messages = messages[:-1] + [
                HumanMessage(content=f"{user_message}{context_message}")
            ]
        else:
            enriched_messages = messages
    except Exception as e:
        print(f"⚠️ Memory retrieval skipped: {e}")
        enriched_messages = messages
    
    # Get AI response
    response = llm_with_tools.invoke(enriched_messages)
    
    # Save to memory
    memory.store_memory(thread_id, user_message, "user")
    memory.store_memory(thread_id, response.content, "assistant")
    
    return {"messages": [response]}

# ============ Build Graph ============
graph = StateGraph(ChatState)

# Add nodes
graph.add_node("chat_node", chat_node)
graph.add_node("tools", ToolNode(tools.all_tools))

# Add edges
graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

# Compile
chatbot = graph.compile(checkpointer=memory.checkpointer)

print("✅ Chatbot ready!")