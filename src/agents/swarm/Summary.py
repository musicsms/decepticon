from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_summary_prompt
from src.tools.handoff import handoff_to_initial_access, handoff_to_reconnaissance, handoff_to_planner
from src.utils.llm.config_manager import get_current_llm

# store = InMemoryStore(
#     index={
#         "dims": 1536,
#         "embed": "openai:text-embedding-3-small",
#     }
# ) 

from src.utils.mcp.mcp_loader import load_mcp_tools

async def make_summary_agent():
    # 메모리에서 LLM 로드 (없으면 기본값 사용)
    llm = get_current_llm()
    if llm is None:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")
    
    mcp_tools = await load_mcp_tools(agent_name=["summary"])


    swarm_tools = mcp_tools + [
        handoff_to_reconnaissance, 
        handoff_to_initial_access,
        handoff_to_planner,
        # create_manage_memory_tool(namespace=("memories",)),
        # create_search_memory_tool(namespace=("memories",))
    ]

    agent = create_react_agent(
        llm,
        tools=swarm_tools,
        # store=store,
        name="Summary",
        prompt=load_summary_prompt("swarm")
    )
    return agent
