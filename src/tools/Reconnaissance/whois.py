from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool

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