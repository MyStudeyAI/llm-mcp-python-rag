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
        self.id = id
        self.function = {
            "name": function_name,
            "arguments": function_arg
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "function": self.function
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
            api_key=os.getenv("ALIBABA_KEY"),
            base_url=os.getenv("ALIBABA_BASE_URL")
        )

        # 初始化一下
        self.__model = model
        self.__tools = tools or []
        self.__messages = []
        if system_prompt:
            self.__messages.append({"role": "system", "content": system_prompt})
        if context:
            self.__messages.append({"role": "user", "content": context})

    def chat(self, prompt: str = None) -> Dict[str, Any]:
        """
        发送聊天请求并处理流式响应
        
        Args:
            prompt: 用户输入的提示词
            
        Returns:
            包含 content 和 toolCalls 的字典
        """
        log_title('CHAT')
        if prompt:
            self.__messages.append({"role": "user", "content": prompt})

        
        # 准备 API 调用参数
        create_params = {
            "model": self.__model,
            "messages": self.__messages,
            "stream": True,
        }

         # 只有有工具时才添加 tools 参数
        if self.__tools:
            create_params["tools"] = self.__get_tools_definition() # MCP的tool --> openAI的tool
    
        __stream = self.__llm.chat.completions.create(**create_params)

        __content = ''
        __tool_calls: List[ToolCall] = []
        
        # 用于存储流式工具调用的中间状态
        __tool_call_chunks = []
        
        log_title('RESPONSE')
        for __chunk in __stream:
            if not __chunk.choices:
                continue

            __delta = __chunk.choices[0].delta

            # 处理普通内容
            if __delta.content:
                __content_chunk = __delta.content or ""
                __content += __content_chunk
                sys.stdout.write(__content_chunk)
                sys.stdout.flush()

            # 处理工具调用
            if __delta.tool_calls:
                for __tool_call_chunk in __delta.tool_calls:
                    __index = __tool_call_chunk.index
                    
                    # 确保有足够的空间存储工具调用
                    while len(__tool_call_chunks) <= __index:
                        __tool_call_chunks.append({
                            "id": "",
                            "name": "",
                            "arguments": ""
                        })
                    
                    # 更新工具调用信息
                    if __tool_call_chunk.id:
                        __tool_call_chunks[__index]["id"] = __tool_call_chunk.id
                    
                    if __tool_call_chunk.function and __tool_call_chunk.function.name:
                        __tool_call_chunks[__index]["name"] = __tool_call_chunk.function.name
                    
                    if __tool_call_chunk.function and __tool_call_chunk.function.arguments:
                        __tool_call_chunks[__index]["arguments"] += __tool_call_chunk.function.arguments

        # 将收集到的工具调用转换为 ToolCall 对象
        for __tool_data in __tool_call_chunks:
            if __tool_data["id"] and __tool_data["name"]:
                try:
                    # 尝试解析参数以确保 JSON 有效性
                    json.loads(__tool_data["arguments"])
                except json.JSONDecodeError:
                    # 如果参数不是有效的 JSON，将其包装为字符串
                    __tool_data["arguments"] = json.dumps({"input": __tool_data["arguments"]})
                
                __tool_calls.append(ToolCall(
                    id=__tool_data["id"],
                    function_name=__tool_data["name"],
                    function_arg=__tool_data["arguments"]
                ))

        # 更新消息历史
        if __tool_calls:
            self.__messages.append({
                "role": "assistant",
                "content": __content,
                "tool_calls": [
                    {
                        "id": __tc.id,
                        "function": __tc.function,
                        "type": "function"
                    }
                    for __tc in __tool_calls
                ]
            })
        elif __content:  # 只有内容没有工具调用
            self.__messages.append({
                "role": "assistant",
                "content": __content
            })

        return {"content": __content, "toolCalls": [__tc.to_dict() for __tc in __tool_calls]}

    # 工具结果 ---> tool_message
    def append_tool_result(self, tool_call_id: str, tool_output: str):
        """
        将工具执行结果添加到消息历史
        
        Args:
            tool_call_id: 工具调用 ID
            tool_output: 工具执行结果
        """
        self.__messages.append({
            "role": 'tool',
            "content": tool_output,
            "tool_call_id": tool_call_id
        })

    def __get_tools_definition(self) -> List[Dict[str, Any]]:
        __result = []
        for __tool in self.__tools:
            # 将 MCP 工具格式转换为 OpenAI 格式
            __function_def = {
                "name": __tool["name"],
                "description": __tool.get("description", ""),
                "parameters": __tool.get("inputSchema", {})
            }
            __result.append({
                "type": 'function',
                "function": __function_def
            })
        return __result
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取消息历史"""
        return self.__messages.copy()


def example():
    # 创建聊天实例
    chat = ChatOpenAI(
        model="glm-4.7",
        system_prompt="你是一个有用的助手"
    )
    
    # 发送消息
    response = chat.chat("今天北京天气怎么样？")
    
    print(f"\n助理回复: {response['content']}")
    
    # 如果有工具调用，模拟执行并添加结果
    if response["toolCalls"]:
        # 继续对话
        print("\n工具执行完成，继续对话...")
        response2 = chat.chat("谢谢，告诉我湿度是多少？")
        print(f"助理回复: {response2['content']}")
    
    print(f"\n最终消息历史长度: {len(chat.get_messages())}")


# 使用示例
if __name__ == "__main__":
    example()