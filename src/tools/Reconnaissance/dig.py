from tools.command_execution import command_execution
from typing_extensions import Annotated
from langchain.tools import tool

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