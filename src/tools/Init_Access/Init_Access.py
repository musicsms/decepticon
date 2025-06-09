from src.tools.command_execution import command_execution
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
            args_str += " -o \"StrictHostKeyChecking=no\" -o \"HostKeyAlgorithms=ssh-rsa\""
        else:
            args_str = "-o \"StrictHostKeyChecking=no\" -o \"HostKeyAlgorithms=ssh-rsa\""
        
    # Construct the sshpass command with SSH
    command = f'sshpass -p "{password}" ssh {args_str} {user}@{target}'
    
    # Execute the command through the command_execution tool
    return command_execution.invoke(command)