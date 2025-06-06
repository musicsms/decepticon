from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool
from typing import List, Optional, Union

@tool
def nmap(target: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "command execution Result"]:
    """
    A simple nmap tool to scan a specified target.

    Args:
        target: The target host or IP address to scan
        options: Additional arguments to pass to the nmap command, can be a string or list of strings

    Returns:
        str: The output of running the nmap command
    """
    # Handle both string and list arguments
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options
        
    command = f'nmap {args_str} {target}'
    return command_execution.invoke(command)