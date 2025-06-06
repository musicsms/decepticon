from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool
from typing import List, Optional, Union

@tool
def hydra(target: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
    """
    Brute force tool for password attacks against various services.
    
    This tool attempts brute force password attacks against specified targets using
    provided wordlists and attack parameters.
    
    Args:
        target (str): The target specification (e.g., ssh://example.com or http-post-form://example.com/login.php)
        options (str or list): Command arguments for hydra (e.g., "-l admin -P /usr/share/wordlists/rockyou.txt")
        
    Returns:
        str: Results of the hydra attack attempt showing successful credentials if found
    """
    # Handle both string and list arguments
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options
        
    command = f'hydra {args_str} {target}'
    return command_execution.invoke(command)