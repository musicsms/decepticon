from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_initaccess_prompt
from src.tools.handoff import handoff_to_planner, handoff_to_reconnaissance, handoff_to_summary
from src.utils.llm.config_manager import get_current_llm

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small",
    }
) 

from src.utils.mcp.mcp_loader import load_mcp_tools

async def make_initaccess_agent():

    llm = get_current_llm()
    if llm is None:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")
    
    mcp_tools = await load_mcp_tools(agent_name=["initial_access"])

        
    swarm_tools = mcp_tools + [
        handoff_to_reconnaissance,
        handoff_to_planner,
        handoff_to_summary,
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",))
    ]

    agent = create_react_agent(
        llm,
        tools=swarm_tools,
        store=store,
        name="Initial_Access",
        prompt=load_initaccess_prompt("swarm")
    )
    return agent



