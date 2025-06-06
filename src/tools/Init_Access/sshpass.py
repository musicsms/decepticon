from src.tools.Init_Access.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool
from typing import List, Optional, Union

@tool
def sshpass(target: str, user: str, password: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
    """
    Non-interactive SSH password authentication tool.
    
    This tool uses sshpass to provide password authentication for SSH connections in a non-interactive way,
    allowing for automated SSH connections with password authentication.
    
    Args:
        target (str): The target IP or hostname to connect to (e.g., "example.com" or "192.168.1.10")
        user (str): The username to authenticate with (e.g., "root", "admin", "kali")
        password (str): The password to use for authentication
        options (str or list): Additional SSH command options (e.g., "-p 2222" for custom port, "-i key.pem" for identity file)
        
    Returns:
        str: Results of the SSH connection attempt or command execution
        
    Examples:
        - sshpass("192.168.1.10", "root", "toor")
        - sshpass("example.com", "admin", "P@ssw0rd", "-p 2222")
    """
    # Handle both string and list arguments
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options
    
    # Always disable StrictHostKeyChecking for automated connections unless explicitly specified
    if "StrictHostKeyChecking" not in str(options):
        if args_str:
            args_str += " -o \"StrictHostKeyChecking=no\""
        else:
            args_str = "-o \"StrictHostKeyChecking=no\""
        
    # Construct the sshpass command with SSH
    command = f'sshpass -p "{password}" ssh {args_str} {user}@{target}'
    
    # Execute the command through the command_execution tool
    return command_execution.invoke(command)
