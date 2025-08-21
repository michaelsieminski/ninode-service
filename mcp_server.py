#!/usr/bin/env python3
"""
Ninode MCP Server
MCP (Model Context Protocol) server for interacting with ninode-service instances
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field


class NinodeConfig(BaseModel):
    """Configuration for connecting to a ninode-service instance"""

    name: str = Field(..., description="Human-readable name for this server")
    url: str = Field(..., description="Base URL of the ninode-service")
    api_key: str = Field(..., description="API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class NinodeMCPServer:
    """MCP Server for ninode-service integration"""

    def __init__(self):
        self.servers: Dict[str, NinodeConfig] = {}
        self.server = Server("ninode-mcp")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="ninode_get_status",
                    description="Get system status from a ninode-service instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the configured ninode server",
                            }
                        },
                        "required": ["server_name"],
                    },
                ),
                types.Tool(
                    name="ninode_get_metrics",
                    description="Get system metrics (CPU, memory, disk, load) from a ninode-service instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the configured ninode server",
                            }
                        },
                        "required": ["server_name"],
                    },
                ),
                types.Tool(
                    name="ninode_execute_command",
                    description="Execute a system command on a ninode-service instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the configured ninode server",
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute (must be from allowed list)",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                                "default": [],
                            },
                        },
                        "required": ["server_name", "command"],
                    },
                ),
                types.Tool(
                    name="ninode_trigger_update",
                    description="Trigger a manual update check and update if available",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the configured ninode server",
                            }
                        },
                        "required": ["server_name"],
                    },
                ),
                types.Tool(
                    name="ninode_health_check",
                    description="Check if a ninode-service instance is healthy and responding",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the configured ninode server",
                            }
                        },
                        "required": ["server_name"],
                    },
                ),
                types.Tool(
                    name="ninode_list_servers",
                    description="List all configured ninode servers",
                    inputSchema={"type": "object", "properties": {}},
                ),
                types.Tool(
                    name="ninode_configure_server",
                    description="Add or update a ninode server configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Unique name for this server",
                            },
                            "url": {
                                "type": "string",
                                "description": "Base URL of the ninode-service",
                            },
                            "api_key": {
                                "type": "string",
                                "description": "API key for authentication",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Request timeout in seconds",
                                "default": 30,
                            },
                        },
                        "required": ["name", "url", "api_key"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "ninode_list_servers":
                    return await self._list_servers()
                elif name == "ninode_configure_server":
                    return await self._configure_server(arguments)
                elif name == "ninode_health_check":
                    return await self._health_check(arguments["server_name"])
                elif name == "ninode_get_status":
                    return await self._get_status(arguments["server_name"])
                elif name == "ninode_get_metrics":
                    return await self._get_metrics(arguments["server_name"])
                elif name == "ninode_execute_command":
                    return await self._execute_command(
                        arguments["server_name"],
                        arguments["command"],
                        arguments.get("args", []),
                    )
                elif name == "ninode_trigger_update":
                    return await self._trigger_update(arguments["server_name"])
                else:
                    return [
                        types.TextContent(type="text", text=f"Unknown tool: {name}")
                    ]
            except Exception as e:
                return [
                    types.TextContent(
                        type="text", text=f"Error executing {name}: {str(e)}"
                    )
                ]

    async def _make_request(
        self,
        server_name: str,
        endpoint: str,
        method: str = "GET",
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to ninode-service"""
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not configured")

        config = self.servers[server_name]
        url = urljoin(config.url.rstrip("/") + "/", endpoint.lstrip("/"))

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

    async def _list_servers(self) -> Sequence[types.TextContent]:
        """List configured servers"""
        if not self.servers:
            return [
                types.TextContent(
                    type="text",
                    text="No servers configured. Use ninode_configure_server to add servers.",
                )
            ]

        server_list = []
        for name, config in self.servers.items():
            server_list.append(f"- {name}: {config.url}")

        return [
            types.TextContent(
                type="text",
                text="Configured ninode servers:\n" + "\n".join(server_list),
            )
        ]

    async def _configure_server(
        self, args: Dict[str, Any]
    ) -> Sequence[types.TextContent]:
        """Configure a new server"""
        config = NinodeConfig(**args)
        self.servers[config.name] = config

        return [
            types.TextContent(
                type="text",
                text=f"Server '{config.name}' configured successfully at {config.url}",
            )
        ]

    async def _health_check(self, server_name: str) -> Sequence[types.TextContent]:
        """Check server health"""
        try:
            result = await self._make_request(server_name, "/health")
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ Server '{server_name}' is healthy: {json.dumps(result, indent=2)}",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Server '{server_name}' health check failed: {str(e)}",
                )
            ]

    async def _get_status(self, server_name: str) -> Sequence[types.TextContent]:
        """Get system status"""
        result = await self._make_request(server_name, "/status")
        return [
            types.TextContent(
                type="text",
                text=f"System Status for '{server_name}':\n{json.dumps(result, indent=2)}",
            )
        ]

    async def _get_metrics(self, server_name: str) -> Sequence[types.TextContent]:
        """Get system metrics"""
        result = await self._make_request(server_name, "/metrics")

        # Format metrics nicely
        formatted_output = [f"System Metrics for '{server_name}':"]

        if "memory" in result:
            mem = result["memory"]
            formatted_output.append(f"\n📊 Memory:")
            formatted_output.append(f"  Total: {mem.get('total_gb', 0)} GB")
            formatted_output.append(
                f"  Used: {mem.get('used_gb', 0)} GB ({mem.get('usage_percent', 0)}%)"
            )
            formatted_output.append(f"  Available: {mem.get('available_gb', 0)} GB")

        if "disk" in result:
            formatted_output.append(f"\n💾 Disk Usage:")
            for disk in result["disk"]:
                formatted_output.append(
                    f"  {disk['mount_point']}: {disk['used']}/{disk['size']} ({disk['usage_percent']}%)"
                )

        if "system" in result:
            sys_info = result["system"]
            formatted_output.append(f"\n⚡ System:")
            if "uptime" in sys_info:
                formatted_output.append(f"  Uptime: {sys_info['uptime']}")
            if "load_average" in sys_info:
                load = sys_info["load_average"]
                formatted_output.append(
                    f"  Load: {load.get('1min', 0):.2f}, {load.get('5min', 0):.2f}, {load.get('15min', 0):.2f}"
                )

        return [types.TextContent(type="text", text="\n".join(formatted_output))]

    async def _execute_command(
        self, server_name: str, command: str, args: List[str]
    ) -> Sequence[types.TextContent]:
        """Execute a system command"""
        payload = {"command": command, "args": args}

        result = await self._make_request(server_name, "/execute", "POST", payload)

        output_lines = [f"Command execution on '{server_name}':"]
        output_lines.append(f"Command: {result['command']}")
        output_lines.append(f"Exit Code: {result['exit_code']}")

        if result.get("stdout"):
            output_lines.append(f"\nSTDOUT:\n{result['stdout']}")

        if result.get("stderr"):
            output_lines.append(f"\nSTDERR:\n{result['stderr']}")

        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def _trigger_update(self, server_name: str) -> Sequence[types.TextContent]:
        """Trigger manual update"""
        result = await self._make_request(server_name, "/update", "POST")

        if result.get("status") == "updating":
            message = f"🔄 Update initiated on '{server_name}': {result['from_version']} → {result['to_version']}"
        elif result.get("status") == "up_to_date":
            message = f"✅ Server '{server_name}' is already up to date (version {result['current_version']})"
        else:
            message = (
                f"Update response from '{server_name}': {json.dumps(result, indent=2)}"
            )

        return [types.TextContent(type="text", text=message)]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, {})


def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    mcp_server = NinodeMCPServer()
    asyncio.run(mcp_server.run())


if __name__ == "__main__":
    main()
