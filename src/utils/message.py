from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from rich import markup

# 도구 이름 
def parse_tool_name(tool_name: str) -> str:
    """Parse tool name simply (no hardcoding)"""
    # 1. Handle transfer_to_ prefix
    if tool_name.startswith("transfer_to_"):
        target_agent = tool_name.replace("transfer_to_", "").replace("_", " ").title()
        return f"Transfer to {target_agent}"
    
    # 2. Convert snake_case to Title Case
    return tool_name.replace("_", " ").title()

# 에이전트 이름 from namespace
def get_agent_name(namespace):
    """Namespace에서 에이전트 이름 추출"""
    if not namespace:
        return "Unknown"
    
    if len(namespace) > 0:
        namespace_str = namespace[0]
        if ':' in namespace_str:
            return namespace_str.split(':')[0]
    
    return "Unknown"

# 메시지 타입
def get_message_type(message):
    """메시지 타입 파싱"""
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "ai"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return None

# 메시지 content 
def extract_message_content(message):
    """메시지에서 내용 추출 - Rich 마크업 안전 처리"""
    try:
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = str(message)
        
        if isinstance(content, str):
            # Rich 마크업을 안전하게 escape 처리
            return markup.escape(content)
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text' and 'text' in item:
                        text_parts.append(markup.escape(item['text']))
                    elif 'text' in item:
                        text_parts.append(markup.escape(item['text']))
                elif isinstance(item, str):
                    text_parts.append(markup.escape(item))
            return "\n".join(text_parts) if text_parts else markup.escape(str(content))
        else:
            return markup.escape(str(content))
    except Exception as e:
        error_msg = f"Content extraction error: {str(e)}\n{str(message)}"
        return markup.escape(error_msg)
