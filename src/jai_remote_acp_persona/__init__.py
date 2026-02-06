"""Jupyter AI persona that connects to a remote ACP server."""

__version__ = "0.1.0"

from .remote_acp_client import RemoteAcpClient
from .remote_acp_persona import RemoteAcpPersona
from .example_persona import ExampleRemotePersona

__all__ = [
    "RemoteAcpClient",
    "RemoteAcpPersona",
    "ExampleRemotePersona",
]
