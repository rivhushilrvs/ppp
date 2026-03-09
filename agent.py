import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph
from langgraph.constants import END
from langgraph.graph.message import add_messages
from crypto_tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are CryptoBot — a sharp, knowledgeable crypto assistant with real-time market access.

You have access to these tools:
- get_crypto_prices: Live prices + 24h % change for top 10 coins
- get_single_coin_price: Detailed price data for any specific coin
- get_crypto_news: Latest trending crypto news headlines
- get_market_summary: Global market cap, BTC dominance, total volume
- get_price_trend: Analyzes signals to predict if a coin will RISE or FALL

GUIDELINES:
- ALWAYS call the relevant tool first before answering
- When user asks if price will rise/fall/go up/go down — ALWAYS use get_price_trend
- Present the verdict clearly: LIKELY TO RISE or LIKELY TO FALL
- List each signal as a bullet point
- Show the confidence level (High / Moderate / Low)
- Always add: "⚠️ This is signal-based analysis, not financial advice."
- Format prices with $ and commas
- Show changes with ▲ for gains and ▼ for losses
- Keep tone sharp, confident, and clear"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_tokens=2048,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tools_by_name = {t.name: t for t in ALL_TOOLS}

    def call_model(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def call_tools(state: AgentState):
        last_msg = state["messages"][-1]
        results = []
        for tool_call in last_msg.tool_calls:
            try:
                tool = tools_by_name[tool_call["name"]]
                result = tool.invoke(tool_call["args"])
            except Exception as e:
                result = f"Tool error: {str(e)}"
            results.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            ))
        return {"messages": results}

    def should_continue(state: AgentState):
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and len(last_msg.tool_calls) > 0:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", call_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


agent = build_agent()


def chat(message: str, history: list = None) -> str:
    messages = []
    if history:
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=message))

    result = agent.invoke({"messages": messages})
    last = result["messages"][-1]
    return last.content