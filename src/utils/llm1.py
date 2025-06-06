# DEPRECATED: This file is deprecated. Use src.utils.llm.models instead.
# See src/utils/llm/README.md for migration guide.

import warnings
warnings.warn(
    "src.utils.llm1 is deprecated. Use 'from src.utils.llm import load_llm' instead. "
    "See src/utils/llm/README.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

GPT4o_MINI = "gpt-4o-mini"
GPT4o = "gpt-4o"
O1_PREVIEW = "o1-preview"
O1_MINI = "o1-mini"
SONNET_37 = "claude-3-7-sonnet-latest"
SONNET_35 = "claude-3-5-sonnet-latest"


OPENAI_SUPERVISOR_LLM = ChatOpenAI(model=GPT4o, temperature=0)
OPENAI_AGENT_LLM = ChatOpenAI(model=GPT4o_MINI, temperature=0)
CLAUDE_AGENT_LLM = ChatAnthropic(model_name=SONNET_35,temperature=0)


CLAUDE_THINKING_LLM = ChatAnthropic(
    model_name=SONNET_37,
    model_kwargs={
        "max_tokens" : 20000,
        "thinking" : {"type": "enabled", "budget_tokens": 1024},
    },
)




