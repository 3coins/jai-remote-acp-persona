import asyncio
from typing import Awaitable, ClassVar

from acp import NewSessionResponse
from acp.schema import AvailableCommand
from jupyter_ai_persona_manager import BasePersona
from jupyterlab_chat.models import Message

from .remote_acp_client import RemoteAcpClient


class RemoteAcpPersona(BasePersona):
    """
    Base persona for remote ACP connections.

    Unlike BaseAcpPersona which spawns local subprocesses, this class connects
    to remote ACP servers via WebSocket. Multiple instances of the same persona
    class share a single client/connection, with each instance having its own
    unique session ID.
    """

    _client_future: ClassVar[Awaitable[RemoteAcpClient] | None] = None
    """
    The future that yields the remote ACP client once complete. This is a class
    attribute because multiple instances of the same ACP persona may share a
    remote client connection.

    Developers should always use `self.get_client()`.
    """

    _client_session_future: Awaitable[NewSessionResponse]
    """
    The future that yields the ACP client session info. Each instance of an ACP
    persona has a unique session ID, i.e. each chat reserves a unique session.

    Developers should always call `self.get_session()` or `self.get_session_id()`.
    """

    _acp_slash_commands: list[AvailableCommand]

    def __init__(self, *args, remote_url: str, **kwargs):
        """
        Initialize remote ACP persona.

        :param remote_url: WebSocket URL for the remote ACP server
            (e.g., "ws://localhost:8080/ws")
        """
        super().__init__(*args, **kwargs)

        self._remote_url = remote_url

        # Ensure each subclass has its own client by checking if the
        # class variable is defined directly on this class (not inherited)
        if '_client_future' not in self.__class__.__dict__ or self.__class__._client_future is None:
            self.__class__._client_future = self.event_loop.create_task(
                self._init_client()
            )

        self._client_session_future = self.event_loop.create_task(
            self._init_client_session()
        )
        self._acp_slash_commands = []

    async def _init_client(self) -> RemoteAcpClient:
        """Initialize the remote ACP client."""
        client = RemoteAcpClient(remote_url=self._remote_url, event_loop=self.event_loop)
        self.log.info(f"Initialized remote ACP client for '{self.__class__.__name__}' at {self._remote_url}")
        return client

    async def _init_client_session(self) -> NewSessionResponse:
        """Create a new session with the remote ACP server."""
        client = await self.get_client()
        session = await client.create_session(persona=self)
        self.log.info(
            f"Initialized new remote ACP session for '{self.__class__.__name__}'"
            f" with ID '{session.session_id}'."
        )
        return session

    async def get_client(self) -> RemoteAcpClient:
        """
        Safely returns the remote ACP client for this persona.
        """
        return await self.__class__._client_future

    async def get_session(self) -> NewSessionResponse:
        """
        Safely returns the ACP client session for this chat.
        """
        return await self._client_session_future

    async def get_session_id(self) -> str:
        """
        Safely returns the ACP client ID assigned to this chat.
        """
        session = await self._client_session_future
        return session.session_id

    async def process_message(self, message: Message) -> None:
        """
        A default implementation for the `BasePersona.process_message()` method
        for remote ACP agents.

        This method may be overridden by child classes.
        """
        client = await self.get_client()
        session_id = await self.get_session_id()

        # TODO: add attachments!
        prompt = message.body.replace("@" + self.as_user().mention_name, "").strip()
        await client.prompt_and_reply(
            session_id=session_id,
            prompt=prompt,
        )

    @property
    def acp_slash_commands(self) -> list[AvailableCommand]:
        """
        Returns the list of slash commands advertised by the ACP agent in the
        current session.

        This initializes to an empty list, and should be updated **only** by the
        ACP client upon receiving a `session/update` request containing an
        `AvailableCommandsUpdate` payload from the ACP agent.
        """
        return self._acp_slash_commands

    @acp_slash_commands.setter
    def acp_slash_commands(self, commands: list[AvailableCommand]):
        self.log.info(
            f"Setting {len(commands)} slash commands for '{self.name}' in room '{self.parent.room_id}'."
        )
        self._acp_slash_commands = commands

    def shutdown(self):
        """Shutdown the remote connection."""
        self.event_loop.create_task(self._shutdown())

    async def _shutdown(self):
        """Asynchronously close the remote ACP connection."""
        self.log.info(f"Closing remote ACP client for '{self.__class__.__name__}'.")
        client = await self.get_client()
        conn = await client.get_connection()
        await conn.close()

        # Close the connection context if available
        if hasattr(client, '_connection_context') and client._connection_context:
            try:
                await client.close()
            except Exception as e:
                self.log.error(f"Error during connection cleanup: {e}")

        self.log.info(f"Completed closing remote ACP client for '{self.__class__.__name__}'.")
