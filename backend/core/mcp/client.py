"""
MCP Client - Connects to MCP servers and executes tools.

The MCP (Model Context Protocol) allows AI agents to use external tools
via a standardized protocol. This client manages connections to MCP servers
and provides a simple interface for tool execution.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MCPTransportType(Enum):
    """Transport types for MCP communication."""
    STDIO = "stdio"  # Subprocess with stdin/stdout
    HTTP = "http"    # HTTP/SSE transport


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str  # Command to start the server (for stdio)
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: MCPTransportType = MCPTransportType.STDIO
    url: Optional[str] = None  # For HTTP transport


@dataclass
class MCPToolDefinition:
    """Definition of a tool provided by an MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPClient:
    """
    Client for communicating with MCP servers.

    Supports both stdio (subprocess) and HTTP transports.
    Handles JSON-RPC message framing and response parsing.
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._request_id = 0
        self._initialized: Dict[str, bool] = {}

    async def add_server(self, config: MCPServerConfig) -> bool:
        """
        Add and connect to an MCP server.

        Args:
            config: Server configuration

        Returns:
            True if connection successful
            
        Raises:
            ValueError: If command not found or configuration error
            RuntimeError: If connection or initialization fails
        """
        self._servers[config.name] = config

        if config.transport == MCPTransportType.STDIO:
            return await self._connect_stdio(config)
        elif config.transport == MCPTransportType.HTTP:
            return await self._connect_http(config)
        else:
            error_msg = f"Unknown transport type: {config.transport}"
            logger.error(f"MCP server {config.name}: {error_msg}")
            raise ValueError(error_msg)

    async def _connect_stdio(self, config: MCPServerConfig) -> bool:
        """Connect to an MCP server via stdio (subprocess)."""
        process = None
        try:
            # Prepare environment
            env = dict(subprocess.os.environ)
            env.update(config.env)

            # Check if command exists (for npx, node, etc.)
            import shutil
            import os
            command_path = shutil.which(config.command)
            if not command_path:
                error_msg = f"Command '{config.command}' not found. Please ensure Node.js is installed for MCP servers."
                logger.error(f"MCP server {config.name}: {error_msg}")
                raise ValueError(error_msg)

            # On Windows, handle .CMD and .BAT files properly
            # Use the full path from shutil.which() to ensure we can find it
            if sys.platform == "win32" and command_path.lower().endswith(('.cmd', '.bat')):
                # For Windows batch files, use cmd.exe to run them
                # This ensures proper execution of .CMD/.BAT files
                cmd_args = ['cmd.exe', '/c', command_path] + config.args
            else:
                # For executables, use the full path directly
                cmd_args = [command_path] + config.args

            logger.debug(f"MCP server {config.name}: Executing command: {cmd_args[0]} with args: {config.args}")

            # Start the subprocess
            process = subprocess.Popen(
                cmd_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=0,
                text=False,  # Use bytes mode for better compatibility
            )

            # Check if process started successfully
            if process.poll() is not None:
                # Process exited immediately - read stderr for error
                _, stderr_output = process.communicate(timeout=5)
                error_msg = stderr_output.decode('utf-8', errors='replace') if stderr_output else "Process exited immediately"
                logger.error(f"MCP server {config.name} process failed to start: {error_msg}")
                raise RuntimeError(f"Process failed to start: {error_msg}")

            self._processes[config.name] = process

            # Give the process a moment to initialize
            await asyncio.sleep(0.5)

            # Check if process is still running
            if process.poll() is not None:
                # Process died - read stderr
                _, stderr_output = process.communicate(timeout=5)
                error_msg = stderr_output.decode('utf-8', errors='replace') if stderr_output else "Process exited unexpectedly"
                logger.error(f"MCP server {config.name} process exited: {error_msg}")
                raise RuntimeError(f"Process exited: {error_msg}")

            # Initialize the connection
            init_result = await self._send_request(
                config.name,
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                    },
                    "clientInfo": {
                        "name": "NodeAI",
                        "version": "1.0.0",
                    },
                }
            )

            if init_result and "result" in init_result:
                self._initialized[config.name] = True

                # Send initialized notification
                await self._send_notification(config.name, "notifications/initialized", {})

                # List available tools
                await self._refresh_tools(config.name)

                logger.info(f"MCP server {config.name} connected successfully")
                return True
            else:
                # Try to read stderr for more info (non-blocking check)
                error_detail = "Initialization failed"
                if init_result is None:
                    error_detail = "No response from server (timeout or connection issue)"
                elif isinstance(init_result, dict):
                    if "error" in init_result:
                        error_detail = init_result["error"].get("message", str(init_result["error"]))
                    else:
                        error_detail = f"Unexpected response: {init_result}"
                else:
                    error_detail = f"Unexpected response type: {type(init_result)}"
                
                logger.error(f"MCP server {config.name} initialization failed: {error_detail}")
                
                # Try to read stderr for more context (non-blocking)
                stderr_text = ""
                if process:
                    # Check if process is still running
                    if process.poll() is not None:
                        try:
                            _, stderr_output = process.communicate(timeout=2)
                            if stderr_output:
                                stderr_text = stderr_output.decode('utf-8', errors='replace')
                                logger.error(f"MCP server {config.name} stderr: {stderr_text[:1000]}")
                        except Exception as e:
                            logger.debug(f"Could not read stderr: {e}")
                    else:
                        # Process is still running, try to peek at stderr
                        # Note: This is tricky on Windows, so we'll just log what we have
                        logger.debug(f"MCP server {config.name} process still running but initialization failed")
                
                # Build comprehensive error message
                full_error = error_detail
                if stderr_text:
                    full_error = f"{error_detail}\nServer output: {stderr_text[:500]}"
                
                raise RuntimeError(full_error)

        except FileNotFoundError as e:
            error_msg = f"Command not found: {config.command}. Please ensure Node.js is installed."
            logger.error(f"MCP server {config.name}: {error_msg}")
            if process:
                try:
                    process.terminate()
                except:
                    pass
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to connect to MCP server {config.name}: {error_msg}", exc_info=True)
            if process:
                try:
                    # Try to read stderr before terminating
                    try:
                        _, stderr_output = process.communicate(timeout=2)
                        if stderr_output:
                            stderr_text = stderr_output.decode('utf-8', errors='replace')
                            logger.error(f"MCP server {config.name} stderr: {stderr_text}")
                            error_msg = f"{error_msg}\nStderr: {stderr_text[:500]}"
                    except:
                        process.terminate()
                except:
                    pass
            raise RuntimeError(error_msg) from e

    async def _connect_http(self, config: MCPServerConfig) -> bool:
        """Connect to an MCP server via HTTP."""
        # HTTP transport implementation
        # TODO: Implement HTTP/SSE transport
        logger.warning(f"HTTP transport not yet implemented for {config.name}")
        return False

    async def _send_request(
        self,
        server_name: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to an MCP server."""
        if server_name not in self._processes:
            logger.error(f"Server {server_name} not connected")
            return None

        process = self._processes[server_name]

        # Check if process is still alive
        if process.poll() is not None:
            logger.error(f"Server {server_name} process has exited (code: {process.returncode})")
            # Try to read stderr
            try:
                _, stderr_output = process.communicate(timeout=1)
                if stderr_output:
                    stderr_text = stderr_output.decode('utf-8', errors='replace')
                    logger.error(f"Server {server_name} stderr: {stderr_text[:500]}")
            except:
                pass
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            logger.debug(f"Sending to {server_name}: {request_str.strip()}")
            process.stdin.write(request_str.encode())
            process.stdin.flush()

            # Read response (with timeout)
            response_line = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, process.stdout.readline
                ),
                timeout=30.0
            )

            if response_line:
                response_text = response_line.decode('utf-8', errors='replace').strip()
                logger.debug(f"Received from {server_name}: {response_text[:200]}")
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response from {server_name}: {e}\nResponse: {response_text[:500]}")
                    return None
            else:
                logger.warning(f"No response from {server_name} for method {method}")
                # Check if process died
                if process.poll() is not None:
                    try:
                        _, stderr_output = process.communicate(timeout=1)
                        if stderr_output:
                            stderr_text = stderr_output.decode('utf-8', errors='replace')
                            logger.error(f"Server {server_name} died with stderr: {stderr_text[:500]}")
                    except:
                        pass
                return None

        except asyncio.TimeoutError:
            logger.error(f"Request to {server_name} timed out after 30s")
            # Check if process is still alive
            if process.poll() is not None:
                try:
                    _, stderr_output = process.communicate(timeout=1)
                    if stderr_output:
                        stderr_text = stderr_output.decode('utf-8', errors='replace')
                        logger.error(f"Server {server_name} stderr: {stderr_text[:500]}")
                except:
                    pass
            return None
        except Exception as e:
            logger.error(f"Error sending request to {server_name}: {e}", exc_info=True)
            return None

    async def _send_notification(
        self,
        server_name: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if server_name not in self._processes:
            return

        process = self._processes[server_name]

        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        try:
            notification_str = json.dumps(notification) + "\n"
            process.stdin.write(notification_str.encode())
            process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending notification to {server_name}: {e}")

    async def _refresh_tools(self, server_name: str) -> None:
        """Refresh the list of tools from a server."""
        result = await self._send_request(server_name, "tools/list", {})

        if result and "result" in result:
            tools = result["result"].get("tools", [])
            for tool in tools:
                tool_def = MCPToolDefinition(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    input_schema=tool.get("inputSchema", {}),
                    server_name=server_name,
                )
                # Store with server prefix to avoid conflicts
                full_name = f"{server_name}.{tool['name']}"
                self._tools[full_name] = tool_def

            logger.info(f"Loaded {len(tools)} tools from {server_name}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server.

        Args:
            tool_name: Full tool name (server.tool_name) or just tool_name
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        # Find the tool
        tool_def = None

        # Try full name first
        if tool_name in self._tools:
            tool_def = self._tools[tool_name]
        else:
            # Try to find by short name
            for full_name, t in self._tools.items():
                if t.name == tool_name:
                    tool_def = t
                    break

        if not tool_def:
            return {
                "error": f"Tool {tool_name} not found",
                "available_tools": list(self._tools.keys()),
            }

        # Call the tool
        result = await self._send_request(
            tool_def.server_name,
            "tools/call",
            {
                "name": tool_def.name,
                "arguments": arguments,
            }
        )

        if result and "result" in result:
            return result["result"]
        elif result and "error" in result:
            return {"error": result["error"]}
        else:
            return {"error": "Unknown error calling tool"}

    def get_available_tools(self) -> List[MCPToolDefinition]:
        """Get list of all available tools."""
        return list(self._tools.values())

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a tool."""
        if tool_name in self._tools:
            return self._tools[tool_name].input_schema
        return None

    async def disconnect_server(self, server_name: str) -> None:
        """Disconnect from an MCP server."""
        if server_name in self._processes:
            process = self._processes[server_name]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self._processes[server_name]

        if server_name in self._servers:
            del self._servers[server_name]

        if server_name in self._initialized:
            del self._initialized[server_name]

        # Remove tools from this server
        self._tools = {
            k: v for k, v in self._tools.items()
            if v.server_name != server_name
        }

        logger.info(f"Disconnected from MCP server {server_name}")

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        server_names = list(self._servers.keys())
        for name in server_names:
            await self.disconnect_server(name)


# Singleton instance for global access
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
