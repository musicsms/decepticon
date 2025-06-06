from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool
from typing import List, Optional, Union


@tool
def curl(target: str = "", options: str = "")  -> Annotated[str, "command execution Result"]:
    """
    A simple curl tool to make HTTP requests to a specified target.

    Args:
        args: Additional arguments to pass to the curl command
        target: The target URL to request

    Returns:
        str: The output of running the curl command
    """
    command = f'curl {options} {target}'
    return command_execution(command)

@tool
def dig(target: str, options: str = "") -> Annotated[str, "command execution Result"]:
    """
    DNS lookup tool to retrieve DNS records for a specified domain.
    
    This tool performs DNS queries using specified arguments and target domain to obtain
    information about various DNS records such as A, MX, NS, TXT, etc.
    
    Args:
        target (str): The domain name to query (e.g., example.com)
        options (str): Command arguments for the dig operation (e.g., "MX", "A", "ANY")
        
    Returns:
        str: Formatted results of the DNS lookup operation showing requested DNS records
    """

    command = f'dig {options} {target}'
    return command_execution.invoke(command)

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

@tool
def whois(target: str, options: str = "") -> Annotated[str, "command execution Result"]:
    """
    WHOIS lookup tool to retrieve registration information for a domain.
    
    This tool queries WHOIS databases to obtain information about domain registration,
    including owner contact details, registrar information, creation date, expiration date,
    and name servers.
    
    Args:
        target (str): The domain name or IP address to query (e.g., example.com)
        options (str): Command arguments for the WHOIS operation (e.g., "-h", "-I")
        
    Returns:
        str: Formatted results of the WHOIS lookup containing domain registration details
    """

    command = f'whois {options} {target}'
    return command_execution.invoke(command)