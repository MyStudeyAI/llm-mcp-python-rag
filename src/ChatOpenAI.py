import json
import os
import sys
from typing import Any, Dict, List
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_title


# 加载环境变量
load_dotenv()


class ToolCall:
    """工具调用类"""
    def __init__(self, id: str, function_name: str, function_arg: str):
        self.__id = id
        self.__function = {
            "name" : function_name,
            "arguments":function_arg
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.__id,
            "function": self.__function
        }
    


class ChatOpenAI:
    """OpenAI 聊天客户端类"""

    def __init__(self, model: str, system_prompt: str = '', tools: List[Dict] = None, context: str = ''):
        """
        初始化 OpenAI 聊天客户端
        
        Args:
            model: 模型名称
            system_prompt: 系统提示词
            tools: 来自 MCP 的工具列表
            context: 上下文
        """
        self.__llm = OpenAI(
            api_key= os.getenv("ALIBABA_KEY"),
            base_url= os.getenv("ALIBABA_BASE_URL")
        )

        # 初始化一下
        self.__model = model
        self.__tools = tools or []
        self.__messages = []
        if system_prompt :
            self.messages.append({"role": "system", "content": system_prompt})
        if context:
            self.messages.append({"role": "user", "content": context})

    
    async def chat(self, prompt:str = None) -> Dict[str, Any]:
        """
        发送聊天请求并处理流式响应
        
        Args:
            prompt: 用户输入的提示词
            
        Returns:
            包含 content 和 toolCalls 的字典
        """
        log_title('CHAT')
        if prompt:
            self.__messages.append({"role": "system", "content": prompt})
        
        __strem = await self.__llm.responses.create(
            model=self.__model, 
            messages=self.__messages,
            stream=True,
            tools= self._getToolsDefinition(), # MCP的tool --> openAI的tool
        )

        __content = ''
        __tool_calls: List[ToolCall] = []
        log_title('RESPONES')
        for __chunk in __strem:
            if not __chunk.choices:
                continue

            __delta = __chunk.choices[0].delta

            # 处理普通内容
            if __delta.content:
                content_chunk = __delta.content or ""
                content += content_chunk
                sys.stdout.write(content_chunk)
                sys.stdout.flush()

            # 处理工具调用
            if __delta.tool_calls:
                for __tool_call_chunk in __delta.tool_calls:
                    index = __tool_call_chunk.index

                    # 如果是新的工具调用,创建新的中间状态
                    if len(__tool_call_chunk) <= index:
                        __tool_call_chunk.append({"id": "", "function_name": "", "arguments": ""})


                    __current_call = __tool_call_chunk[index]

                    if __tool_call_chunk.id:
                        __current_call["id"] += __tool_call_chunk.id
                    
                    if __tool_call_chunk.function and __tool_call_chunk.function.name:
                        __current_call["function_name"] += __tool_call_chunk.function.name
                    
                    if __tool_call_chunk.function and __tool_call_chunk.function.arguments:
                        __current_call["arguments"] += __tool_call_chunk.function.arguments


        # 清理工具调用参数，确保 JSON 有效性
        self.__messages.append({
            "role": "assistant",
            "content": __content,
            "tool_calls": [
                {
                    "type": "function",
                    "id": __tool_call.id,
                    "function": {
                        "name": __tool_call.function.name,
                        "arguments": __tool_call.function.arguments,
                    },
                }
                for __tool_call in __tool_calls
            ],
        })
        # self.__messages.append({
        #     "role": "assistant",
        #     "content": __content,
        #     "tool_calls": [
        #         {
        #             "type":'function'
        #             "id": __tool_call.id,
        #             "function": {
        #                 "name": __tool_call.function.name,
        #                 "arguments": __tool_call.function.arguments,
        #             },
        #         }
        #         for __tool_call in __tool_calls
        #     ],
        # })

        return { __content, __tool_calls }
            


    # 工具结果 ---> tool_message
    def append_tool_result(self, tool_call_id: str, tool_out_put: str):
        """
        将工具执行结果添加到消息历史
        
        Args:
            tool_call_id: 工具调用 ID
            tool_output: 工具执行结果
        """
        self.__messages.append({"role":'tool', "content": tool_out_put, "tool_call_id": tool_call_id})


    def _getToolsDefinition(self) -> Dict[str,Any]:
        __result = []
        for _tool in self.__tools:
            __result.append({
                type: 'function',
                function: _tool,
            })
        return __result


def example():
    # 定义一些示例工具
    example_tools = [
        {
            "name": "get_weather",
            "description": "获取天气信息",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["location"]
            }
        }
    ]
    
    # 创建聊天实例
    chat = ChatOpenAI(
        model="glm-4.7",
        system_prompt="你是一个有用的助手",
        tools=example_tools
    )
    
    # 发送消息
    response = chat.chat("今天北京天气怎么样？")
    
    # 如果有工具调用，模拟执行并添加结果
    if response["toolCalls"]:
        for tool_call in response["toolCalls"]:
            print(f"\n调用工具: {tool_call['function']['name']}")
            print(f"参数: {tool_call['function']['arguments']}")
            
            # 模拟工具执行结果
            tool_output = json.dumps({
                "temperature": 25,
                "condition": "晴朗",
                "humidity": "60%"
            })
            
            # 添加工具执行结果
            chat.append_tool_result(tool_call["id"], tool_output)
        
        # 继续对话
        print("\n工具执行完成，继续对话...")
        response2 = chat.chat("谢谢，告诉我湿度是多少？")
    
    print(f"\n最终消息历史长度: {len(chat.get_messages())}")




# 使用示例
if __name__ == "__main__":
    example()