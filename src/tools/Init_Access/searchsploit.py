from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool
from typing import List, Optional, Union

@tool
def searchsploit(service_name: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
    """
    Search for exploits in the Exploit Database by ExploitDB.
    
    This tool searches for exploits, shellcode, and papers in the ExploitDB database
    based on provided search terms such as CVE numbers, product names, or service names.
    
    Args:
        service_name (str): The product, service, or CVE to search for exploits
        options (str or list): Command arguments for searchsploit (e.g., "-t" for title search)
        
    Returns:
        str: Search results listing relevant exploits with their details and paths
    """
    # Handle both string and list arguments
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options
        
    command = f'searchsploit {args_str} {service_name}'
    return command_execution.invoke(command)