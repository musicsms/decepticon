from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langchain_mcp_adapters.client import MultiServerMCPClient
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_planner_prompt
from src.tools.handoff import handoff_to_initial_access, handoff_to_reconnaissance, handoff_to_summary
from src.utils.llm.config_manager import get_current_llm

# store = InMemoryStore(
#     index={
#         "dims": 1536,
#         "embed": "openai:text-embedding-3-small",
#     }
# ) 

from src.utils.mcp.mcp_loader import load_mcp_tools

async def make_planner_agent():
    # planner 에이전트에 연결된 mcp_tools가 없을 수도 있으므로 예외처리 가능
    # 메모리에서 LLM 로드 (없으면 기본값 사용)
    llm = get_current_llm()
    if llm is None:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")
    
    mcp_tools = await load_mcp_tools(agent_name=["planner"])

    swarm_tools = mcp_tools + [
        handoff_to_reconnaissance, 
        handoff_to_initial_access, 
        handoff_to_summary
        # create_manage_memory_tool(namespace=("memories",)),
        # create_search_memory_tool(namespace=("memories",))
    ]

    agent = create_react_agent(
        llm,
        tools=swarm_tools,
        # store=store,
        name="Planner",
        prompt=load_planner_prompt("swarm")
    )
    return agent
