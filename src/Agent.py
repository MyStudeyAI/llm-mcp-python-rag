import asyncio
import json
from pathlib import Path
import shlex
from typing import List, Optional
from ChatOpenAI import ChatOpenAI
from MCPClient import MCPClient
from utils import log_title

class Agent:
    """Agent类，协调MCP工具和LLM的交互"""

    def __init__(self, model: str, mcp_clients: List[MCPClient], system_prompt: str = '', context: str = ''):
        """
        初始化Agent
        
        Args:
            model: LLM模型名称
            mcp_clients: MCP客户端列表
            system_prompt: 系统提示词
            context: 上下文信息
        """
        self.__model = model
        self.__mcp_clients = mcp_clients
        self.__system_prompt = system_prompt
        self.__context = context
        self.__llm: Optional[ChatOpenAI] = None

    
    async def init(self) -> None:
        """初始化agent，包括LLM和所有MCP客户端"""
        log_title("INIT LLM AND TOOLS")
        # 初始化所有MCP客户端
        for __client in self.__mcp_clients:
            await __client.init()

        # 收集所有工具
        __tools = []
        for mcp_client in self.__mcp_clients:
            __tools.extend(mcp_client.get_tools())

        # 初始化语言模型
        self.__llm = ChatOpenAI(self.__model, self.__system_prompt, __tools)

    
    async def close(self) -> None:
        """关闭所有MCP客户端连接"""
        log_title("CLOSE MCP CLIENTS")
        for __client in self.__mcp_clients:
            try:
                # 直接关闭，不添加延迟
                await __client.close()
            except Exception as e:
                print(f"Warning: Error closing client {__client.name if hasattr(__client, 'name') else 'unknown'}: {e}")
    

    async def invoke(self, prompt: str) -> str:
        """
        执行用户提示，处理可能的工具调用链
        
        Args:
            prompt: 用户输入的提示
            
        Returns:
            LLM的最终响应
            
        Raises:
            ValueError: 如果LLM未初始化
        """
        if not self.__llm:
            raise ValueError('LLM is not initialized. Please call init() first.')
        
        __response = await self.__llm.chat(prompt)

        # 这是一个循环,直到没有工具调用为止
        while(True):
            # 处理工具调用
            if __response["tool_calls"] and len(__response["tool_calls"]) > 0:
                for __tool_call in __response["tool_calls"]:
                    __tool_name = __tool_call.get("function", {}).get("name", "")
                    __tool_args = __tool_call.get("function", {}).get("arguments", "")

                    __mcp_client = None
                    __tool_found = False
                    for __client in self.__mcp_clients:
                        tools = __client.get_tools()
                        if tools:
                            for __tool in tools:
                                if __tool.name == __tool_name:
                                    __mcp_client = __client
                                    __tool_found = True
                                    break
                        if __tool_found:
                            break


                    if __mcp_client:
                        log_title(f"TOOL USE {__tool_name}")
                        print(f"Calling tool: {__tool_name} with arguments:")
                        print(f"Raw arguments: {__tool_args}")
                        
                        try:
                            # 解析参数
                            parsed_args = json.loads(__tool_args)
                            __result = await __mcp_client.call_tool(__tool_name, parsed_args)
                            print(f"Tool result type: {type(__result)}")
                            print(f"Tool result: {__result}")
                            
                            # 确保结果是可序列化的
                            if isinstance(__result, dict):
                                result_str = json.dumps(__result)
                            else:
                                # 尝试转换为字典或字符串
                                result_str = json.dumps({"raw_result": str(__result)})
                            
                            # 将工具调用结果传回LLM
                            self.__llm.append_tool_result(__tool_call["id"], result_str)
                            
                        except json.JSONDecodeError as e:
                            error_msg = f"Error parsing tool arguments: {e}"
                            print(error_msg)
                            self.__llm.append_tool_result(__tool_call["id"], json.dumps({"error": error_msg}))
                        except Exception as e:
                            error_msg = f"Error calling tool: {e}"
                            print(error_msg)
                            self.__llm.append_tool_result(__tool_call["id"], json.dumps({"error": error_msg}))
                    else:
                        error_msg = f"Error: No MCPClient found for tool: {__tool_name}"
                        self.__llm.append_tool_result(__tool_call["id"], json.dumps({"error": error_msg}))
                        print(error_msg)
                    
                __response = await self.__llm.chat()

                continue

            
            # 没有工具调用，返回最终结果
            log_title("FINAL RESPONSE")
            await self.close()
            return __response["content"]


async def example():
    
    project_root_dir = Path(__file__).parent.parent
    enabled_mcp_clients = []
    for mcp_name, cmd in [
        (
            "filesystem",
            f"npx -y @modelcontextprotocol/server-filesystem {project_root_dir!s}",
        ),
        (
            "fetch",
            f"uvx mcp-server-fetch".strip(),
        ),
    ]:
        log_title(cmd)
        command, *args = shlex.split(cmd)
        mcp_client = MCPClient(
            name=mcp_name,
            command=command,
            args=args,
        )
        enabled_mcp_clients.append(mcp_client)

    agent = Agent(
        model="glm-4.7",
        mcp_clients=enabled_mcp_clients,
    )
    await agent.init()
    resp = await agent.invoke(
        f"爬取 https://news.ycombinator.com 的内容, 并且总结后保存在 {project_root_dir / 'output'!s} 目录下的news.md文件中"
    )
    log_title(resp)
    await agent.close()


if __name__ == "__main__":
    asyncio.run(example())