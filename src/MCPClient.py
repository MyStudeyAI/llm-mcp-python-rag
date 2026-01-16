import asyncio
from contextlib import AsyncExitStack
from pathlib import Path
import shlex
from typing import Any, List, Optional
from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client

from utils import log_title

class MCPClient:
    def __init__(self, name: str, command: str, args: List[str], version: str = None):
        """
        初始化 MCP 客户端
        
        Args:
            name: 客户端名称
            command: 要执行的命令
            args: 命令参数（必须是字符串列表）
            version: 版本号
        """
        
        # Initialize session and client objects
        self.__session: Optional[ClientSession] = None
        self.__exit_stack: Optional[AsyncExitStack] = None

        # 不需要anthropic,因为有openai
        # self.anthropic = Anthropic()

        """
        npx ...... --nodejs
        uvx ////// --python
        命令分成: command + arguments
        比如: npx @modelcontextprotocol/sdk/client/stdio --log
        """
        self.__name = name
        self.__command = command
        self.__args = [str(arg) for arg in args]  # 确保所有参数都是字符串
        self.__version = version or "0.0.1"
        self.__stdio_transport = None
        self.__tools = []
        self.__initialized = False

    async def close(self):
        """正确关闭所有资源"""
        if self.__exit_stack:
            try:
                await self.__exit_stack.aclose()
            except Exception as e:
                print(f"Warning: Error closing MCP client {self.__name}: {e}")
        self.__initialized = False
    
    async def init(self):
        """初始化 MCP 客户端"""
        if not self.__initialized:
            await self.__connect_to_server()
            self.__initialized = True

    def get_tools(self) -> List[Tool]:
        return self.__tools
    
    async def call_tool(self, tool_name: str, args: dict) -> Any:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            工具执行结果
        """
        if not self.__session:
            raise RuntimeError("MCP client not initialized. Call init() first.")
        
        try:
            # 调用工具
            result = await self.__session.call_tool(tool_name, args)
            return result.content
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            raise

    async def __connect_to_server(self):
        """连接到 MCP 服务器"""
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=self.__command,
            args=self.__args,
        )
        
        try:
            # 创建新的 AsyncExitStack
            self.__exit_stack = AsyncExitStack()
            
            # 创建 stdio 传输
            stdio_transport = await self.__exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.__stdio_transport = stdio_transport
            read_stream, write_stream = stdio_transport
            
            # 创建会话
            self.__session = await self.__exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化会话
            await self.__session.initialize()
            
            # 获取可用工具
            response = await self.__session.list_tools()
            self.__tools = response.tools
            print(f"\nConnected to '{self.__name}' server with tools:", [tool.name for tool in self.__tools])
            
        except Exception as e:
            print(f"Error connecting to server '{self.__name}': {e}")
            await self.close()
            raise


async def example():
    project_root_dir = Path(__file__).parent.parent
    
    # 确保路径是字符串
    fs_path = str(project_root_dir)
    
    clients = []
    
    for mcp_name, cmd in [
        (
            "filesystem",
            f"npx -y @modelcontextprotocol/server-filesystem {shlex.quote(fs_path)}",
        ),
        (
            "fetch",
            "uvx mcp-server-fetch",
        ),
    ]:
        try:
            log_title(mcp_name)
            command, *args = shlex.split(cmd)
            
            mcp_client = MCPClient(
                name=mcp_name,
                command=command,
                args=args,
            )
            
            await mcp_client.init()
            tools = mcp_client.get_tools()
            print(f"Tools for {mcp_name}: {[tool.name for tool in tools]}")
            
            clients.append(mcp_client)
            
        except Exception as e:
            print(f"Failed to initialize {mcp_name}: {e}")
            continue
    
    # 延迟一段时间再关闭，或者在这里进行一些工具调用测试
    try:
        # 等待几秒钟，让服务器有时间处理
        await asyncio.sleep(2)
        
        # 测试调用工具（如果有的话）
        for client in clients:
            if client.get_tools():
                print(f"\nTesting tools for {client.name}:")
                for tool in client.get_tools():
                    print(f"  - {tool.name}")
    
    finally:
        # 关闭所有客户端
        print("\nClosing all clients...")
        for client in clients:
            try:
                await client.close()
            except Exception as e:
                print(f"Error closing client: {e}")


if __name__ == "__main__":
    asyncio.run(example())