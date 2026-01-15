import asyncio
from contextlib import AsyncExitStack
from typing import List, Optional
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
            args: 命令参数
            version: 版本号
        """
        
        # Initialize session and client objects
        self.__session: Optional[ClientSession] = None
        self.__exit_stack = AsyncExitStack()

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
        self.__args = args
        self.__version = version or "0.0.1"
        self.__tools: List[Tool] = []

    
    async def close(self):
        await self.__exit_stack.aclose()
    
    async def init(self):
        await self.__connect_to_server()

    
    def get_tools(self) -> List[Tool]:
        return self.__tools

    
    async def __connect_to_server(self):
        """Connect to an MCP server"""
        
        # 因为有 command + arguments 方式,不需要再拉到本地进行运行
        # is_python = server_script_path.endswith('.py')
        # is_js = server_script_path.endswith('.js')
        # if not (is_python or is_js):
        #     raise ValueError("Server script must be a .py or .js file")

        # command = "python" if is_python else "node"

        __server_params = StdioServerParameters(
            command=self.__command,
            args=self.__args,
        )

        __stdio_transport = await self.__exit_stack.enter_async_context(
            stdio_client(__server_params)
        )
        self.__stdio, self.__write = __stdio_transport
        self.__session = await self.__exit_stack.enter_async_context(
            ClientSession(self.__stdio, self.__write)
        )

        await self.__session.initialize()

        # List available tools
        response = await self.__session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])


async def example():
    # for mcp_name, cmd in [
    #     (
    #         "filesystem",
    #         f"npx -y @modelcontextprotocol/server-filesystem {PROJECT_ROOT_DIR!s}",
    #     ),
    #     (
    #         "fetch",
    #         "uvx mcp-server-fetch",
    #     ),
    # ]:
    #     log_title(mcp_name)
    #     command, *args = shlex.split(cmd)
    #     mcp_client = MCPClient(
    #         name=mcp_name,
    #         command=command,
    #         args=args,
    #     )
    #     await mcp_client.init()
    #     tools = mcp_client.get_tools()
    #     log_title(tools)
    #     await mcp_client.close()

    mcp_client = MCPClient('fetch','uvx',['mcp-server-fetch'])
    await mcp_client.init()
    tools = mcp_client.get_tools()
    log_title(tools)
    await mcp_client.close()



if __name__ == "__main__":
    asyncio.run(example())

