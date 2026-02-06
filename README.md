# Jupyter AI Remote ACP Persona

Connect Jupyter AI to remote ACP (Agent-Client Protocol) servers via WebSocket.

## Overview

This package extends Jupyter AI with support for remote ACP connections. While the standard `jupyter-ai-acp-client` connects to local ACP agent subprocesses, this package enables connections to ACP servers running on remote machines via WebSocket.

## Features

- Connect to remote ACP servers via WebSocket (ws:// or wss://)
- Zero breaking changes to existing stdio-based personas
- Full support for ACP protocol features (file operations, terminal, streaming)
- Easy to extend for custom remote personas
- Configuration via environment variables

## Installation

```bash
uv sync
```

## Usage

### Quick Start

1. Start a remote ACP server (example):

```bash
# See https://github.com/3coins/python-sdk/blob/http-ws-transport/examples/http_echo_agent.py
uv run python examples/http_echo_agent.py
```

2. Set the server URL (optional, defaults to ws://localhost:8080/ws):

```bash
export ACP_SERVER_URL=ws://localhost:8080/ws
```

3. Start Jupyter Lab:

```bash
jupyter lab
```

4. In the chat interface, use the remote persona:

```
@example-remote-acp Hello, remote agent!
```

### Creating Custom Remote Personas

Extend `RemoteAcpPersona` to create your own remote personas:

```python
import os
from pathlib import Path
from jupyter_ai_persona_manager import PersonaDefaults
from jai_remote_acp_persona import RemoteAcpPersona

class MyRemotePersona(RemoteAcpPersona):
    def __init__(self, *args, **kwargs):
        # Get URL from environment or config
        remote_url = os.environ.get("MY_ACP_SERVER_URL", "ws://my-server:8080/ws")
        super().__init__(*args, remote_url=remote_url, **kwargs)

    @property
    def defaults(self) -> PersonaDefaults:
        return PersonaDefaults(
            name="My Remote Agent",
            description="Custom remote ACP agent",
            avatar_path="path/to/avatar.svg",
            system_prompt="Custom system prompt"
        )
```

Register it in `pyproject.toml`:

```toml
[project.entry-points."jupyter_ai.personas"]
my-remote-agent = "mypackage.persona:MyRemotePersona"
```

## Architecture

### Classes

- **`RemoteAcpClient`**: ACP client that connects via WebSocket instead of stdio
- **`RemoteAcpPersona`**: Base class for remote personas (similar to `BaseAcpPersona`)
- **`ExampleRemotePersona`**: Example implementation

### Connection Flow

```
RemoteAcpPersona
  → RemoteAcpClient
    → connect_http_agent(url)
      → ClientSideConnection (WebSocket)
```

### Resource Sharing

- One client per persona class (class-level attribute)
- Multiple persona instances share the same client/connection
- Each instance gets a unique session ID for message routing

## Configuration

### Environment Variables

- `ACP_SERVER_URL`: WebSocket URL for remote ACP server
  - Default: `ws://localhost:8080/ws`
  - Example: `wss://my-server.com:8443/acp`

## Comparison with Stdio Personas

| Feature | Stdio (BaseAcpPersona) | Remote (RemoteAcpPersona) |
|---------|----------------------|--------------------------|
| Connection | Local subprocess | Remote WebSocket |
| Configuration | Executable path | WebSocket URL |
| Use Case | Local CLI tools | Remote servers |
| Protocol | Same ACP protocol | Same ACP protocol |
| Features | All ACP features | All ACP features |

## Requirements

- Python >= 3.12
- agent-client-protocol (with HTTP transport support)
- jupyter-ai
- jupyter-ai-acp-client

## Development

### Project Structure

```
jai-remote-acp-persona/
├── src/
│   └── jai_remote_acp_persona/
│       ├── __init__.py
│       ├── remote_acp_client.py    # WebSocket client
│       ├── remote_acp_persona.py   # Base persona class
│       ├── example_persona.py      # Example implementation
│       └── avatar.svg              # Example avatar
├── pyproject.toml
├── README.md
└── IMPLEMENTATION.md               # Implementation details
```

### Testing

1. Start the example echo server:
```bash
# See https://github.com/3coins/python-sdk/blob/http-ws-transport/examples/http_echo_agent.py
uv python examples/http_echo_agent.py
```

2. In another terminal, test the persona:
```bash
export ACP_SERVER_URL=ws://localhost:8080/ws
jupyter lab
```

3. Use `@example-remote-acp` in the Jupyter AI chat

## Troubleshooting

### Connection Refused

**Problem**: `Failed to connect to remote ACP server`

**Solution**:
- Verify the ACP server is running
- Check the WebSocket URL is correct
- Ensure network connectivity to the server

### Module Not Found

**Problem**: `ModuleNotFoundError: No module named 'acp'`

**Solution**:
- Run `uv sync` to install dependencies
- Verify all git dependencies are accessible

### Invalid URL Format

**Problem**: `ValueError: remote_url must start with ws:// or wss://`

**Solution**:
- Ensure `ACP_SERVER_URL` starts with `ws://` or `wss://`
- Example: `ws://localhost:8080/ws`

## Contributing

This is a reference implementation. Feel free to extend and customize for your needs.

## License

Same as Jupyter AI and ACP SDK licenses.

## See Also

- [Jupyter AI](https://github.com/jupyterlab/jupyter-ai)
- [Jupyter AI ACP Client](https://github.com/jupyter-ai-contrib/jupyter-ai-acp-client)
- [Agent-Client Protocol](https://github.com/3coins/agent-client-protocol)
