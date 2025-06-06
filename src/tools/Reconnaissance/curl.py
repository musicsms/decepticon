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