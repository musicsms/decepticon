# base
from src.prompts.base.summary import BASE_SUMMARY_PROMPT
from src.prompts.base.planner import BASE_PLANNER_PROMPT
from src.prompts.base.recon import BASE_RECON_PROMPT
from src.prompts.base.initaccess import BASE_INITACCESS_PROMPT

# swarm
from src.prompts.swarm.summary import SWARM_SUMMARY_PROMPT
from src.prompts.swarm.planner import SWARM_PLANNER_PROMPT
from src.prompts.swarm.recon import SWARM_RECON_PROMPT
from src.prompts.swarm.initaccess import SWARM_INITACCESS_PROMPT

# tools
from src.prompts.tools.recon_tools import RECON_TOOLS_PROMPT
from src.prompts.tools.initaccess_tools import INITACCESS_TOOLS_PROMPT
from src.prompts.tools.swarm_handoff_tools import SWARM_HANDOFF_TOOLS_PROMPT
from src.prompts.tools.interactive_exec import INTERACTIVE_EXEC_TOOLS_PROMPT

def load_summary_prompt(architecture="swarm"):
    """Summary 에이전트 프롬프트 로드"""
    base_prompt = BASE_SUMMARY_PROMPT
    
    if architecture == "swarm":
        return base_prompt + SWARM_SUMMARY_PROMPT
    else:
        return base_prompt

def load_planner_prompt(architecture="swarm"):
    """Planner 에이전트 프롬프트 로드"""
    base_prompt = BASE_PLANNER_PROMPT
    
    if architecture == "swarm":
        return base_prompt + SWARM_PLANNER_PROMPT
    else:
        return base_prompt

def load_recon_prompt(architecture="swarm"):
    """Reconnaissance 에이전트 프롬프트 로드"""
    base_prompt = BASE_RECON_PROMPT + RECON_TOOLS_PROMPT
    
    if architecture == "swarm":
        return base_prompt + SWARM_RECON_PROMPT + SWARM_HANDOFF_TOOLS_PROMPT
    else:
        return base_prompt

def load_initaccess_prompt(architecture="swarm"):
    """Initial Access 에이전트 프롬프트 로드"""
    base_prompt = BASE_INITACCESS_PROMPT + INITACCESS_TOOLS_PROMPT + INTERACTIVE_EXEC_TOOLS_PROMPT
    
    if architecture == "swarm":
        return base_prompt + SWARM_INITACCESS_PROMPT + SWARM_HANDOFF_TOOLS_PROMPT
    else:
        return base_prompt

def load_supervisor_prompt():
    """Supervisor 에이전트 프롬프트 로드 (hierarchical 아키텍처용)"""
    # supervisor는 별도로 import하지 않았으므로 추가
    from src.prompts.base.supervisor import BASE_SUPERVISOR_PROMPT
    return BASE_SUPERVISOR_PROMPT
