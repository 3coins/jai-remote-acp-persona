import os
from pathlib import Path

from jupyter_ai_persona_manager import PersonaDefaults

from .remote_acp_persona import RemoteAcpPersona


class ExampleRemotePersona(RemoteAcpPersona):
    """
    Example persona demonstrating remote ACP server connection.

    This persona connects to a remote ACP server via WebSocket. The server URL
    can be configured via the ACP_SERVER_URL environment variable, defaulting
    to ws://localhost:8080/ws.

    To use this persona:
    1. Start a remote ACP server (e.g., using acp-python-sdk examples)
    2. Set ACP_SERVER_URL environment variable (optional)
    3. Start Jupyter Lab
    4. Use @example-remote-acp in the chat
    """

    def __init__(self, *args, **kwargs):
        # Get URL from environment or use default
        remote_url = os.environ.get("ACP_SERVER_URL", "ws://localhost:8080/ws")
        super().__init__(*args, remote_url=remote_url, **kwargs)

    @property
    def defaults(self) -> PersonaDefaults:
        # Get avatar path relative to this file
        avatar_path = Path(__file__).parent / "avatar.svg"

        return PersonaDefaults(
            name="Remote ACP Example",
            description="Example persona that connects to a remote ACP server via WebSocket",
            avatar_path=str(avatar_path) if avatar_path.exists() else "",
            system_prompt="You are a helpful AI assistant connected via a remote ACP server."
        )
