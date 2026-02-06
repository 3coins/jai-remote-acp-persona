import asyncio
import logging
from typing import Awaitable, Optional

from acp import PROTOCOL_VERSION
from acp.core import ClientSideConnection
from acp.http import connect_http_agent
from acp.schema import ClientCapabilities, FileSystemCapability, Implementation
from jupyter_ai_acp_client.default_acp_client import JaiAcpClient

logger = logging.getLogger(__name__)


class RemoteAcpClient(JaiAcpClient):
    """
    ACP client for remote WebSocket connections.

    This client connects to a remote ACP server via WebSocket instead of
    spawning a local subprocess. It inherits all protocol method implementations
    from JaiAcpClient and only overrides the connection initialization logic.
    """

    _remote_url: str
    _connection_context: Optional[connect_http_agent]

    def __init__(self, *args, remote_url: str, event_loop: asyncio.AbstractEventLoop, **kwargs):
        """
        Initialize remote ACP client.

        :param remote_url: WebSocket URL for the remote ACP server
            (e.g., "ws://localhost:8080/ws")
        :param event_loop: The asyncio event loop running this process
        """
        # Validate URL format
        if not remote_url or not remote_url.strip():
            raise ValueError("remote_url cannot be empty")

        if not (remote_url.startswith("ws://") or remote_url.startswith("wss://")):
            raise ValueError("remote_url must start with ws:// or wss://")

        self._remote_url = remote_url
        self._connection_context = None

        # Skip JaiAcpClient.__init__ and call grandparent directly
        # This avoids the agent_subprocess requirement
        self.event_loop = event_loop
        self._personas_by_session = {}
        self._queues_by_session = {}

        # Import here to avoid circular dependency
        from jupyter_ai_acp_client.terminal_manager import TerminalManager
        self._terminal_manager = TerminalManager(event_loop)

        # Initialize connection task
        self._connection_future = event_loop.create_task(
            self._init_connection()
        )

        # Call base Client.__init__
        # Note: we skip JaiAcpClient.__init__ to avoid subprocess requirement
        from acp import Client
        Client.__init__(self, *args, **kwargs)

    async def _init_connection(self) -> ClientSideConnection:
        """
        Initialize connection to remote ACP server via WebSocket.

        Overrides the stdio-based connection from JaiAcpClient.
        """
        logger.info(f"Connecting to remote ACP server at {self._remote_url}")

        try:
            # Create connection context manager
            # We need to enter it and keep it alive
            self._connection_context = connect_http_agent(self, self._remote_url)
            conn = await self._connection_context.__aenter__()

            # Initialize protocol
            await conn.initialize(
                protocol_version=PROTOCOL_VERSION,
                client_capabilities=ClientCapabilities(
                    fs=FileSystemCapability(read_text_file=True, write_text_file=True),
                    terminal=True,
                ),
                client_info=Implementation(
                    name="Jupyter AI Remote",
                    title="Jupyter AI Remote ACP Client",
                    version="0.1.0"
                ),
            )

            logger.info(f"Successfully connected to remote ACP server at {self._remote_url}")
            return conn

        except Exception as e:
            logger.error(f"Failed to connect to remote ACP server at {self._remote_url}: {e}")
            raise

    async def close(self):
        """Close the remote connection."""
        if self._connection_context:
            try:
                conn = await self._connection_future
                await self._connection_context.__aexit__(None, None, None)
                logger.info(f"Closed connection to remote ACP server at {self._remote_url}")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
