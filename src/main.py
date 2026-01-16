import asyncio
from pathlib import Path
from typing import List

from Agent import Agent
from EmbeddingRetrieve import EmbeddingRetrieve
from MCPClient import MCPClient
from utils import log_title

# Get the current working directory
current_dir = Path.cwd()


url = "https://jsonplaceholder.typicode.com/users'"
out_path = current_dir / 'output'
task = f"爬取{url}的内容，并总结内容保存到${out_path}/knowledge中，给每个人创建一个md文件，保存基本信息然后告诉我文件的大小是多少字节？"

# Example usage of ChatOpenAI
fetch_mcp = MCPClient('fetch', 'uvx', ['mcp-server-fetch']);

# Example usage of MCPClient for file operations
file_mcp = MCPClient('file', 'npx', ["-y","@modelcontextprotocol/server-filesystem",current_dir]);

async def main():
    prompt = f"根据Chelsey的信息，创作一个关于她的故事，并且把她的故事保存到{out_path}/chelsey_story.md文件中，要包含她的基本信息和故事"
    context = await retrieveContext(prompt);
    agent = Agent('deepseek-v3.2', [fetch_mcp,file_mcp] ,'', context)
    await agent.init()
    
    response = await agent.invoke(prompt)
    
    print('Final Response from Agent:')
    print(response)
    await agent.close()


async def retrieveContext(prompt: str):
    """
    检索上下文：使用RAG从知识库中检索相关内容
    
    Args:
        prompt: 查询提示
        
    Returns:
        检索到的上下文内容
    """

    # RAG
    embedding_retrieves = EmbeddingRetrieve('qwen3-rerank')

    knowledge_dir = out_path / 'knowledge'

    # 确保目录存在（如果不存在则创建）
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # 检查目录是否为空
    if not any(knowledge_dir.iterdir()):
        print(f'知识库目录 {knowledge_dir} 为空，跳过embedding')
        return ""
    
    # 读取文件
    contents: List[str] = []
    has_content = False
    
    try:
        for file_path in knowledge_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():  # 只添加非空内容
                            contents.append(content)
                            has_content = True
                except Exception as e:
                    print(f'读取文件 {file_path} 失败，跳过: {e}')
    except Exception as e:
        print(f'访问目录 {knowledge_dir} 失败: {e}')
    
    if has_content and contents:
        try:
            # 将文档内容添加到向量存储中
            await embedding_retrieves.embed(prompt, contents)
        except Exception as e:
            print(f'Embedding失败: {e}')
            return ""
    else:
        print('跳过embedding: 无有效内容')
        return ""
    
    # 检索上下文
    try:
        context_list = await embedding_retrieves.retrieve(prompt)
        context = '\n'.join(context_list) if context_list else ""
        
        log_title(f'Retrieved Context: {context}')
        print('Retrieved Context:', context)
        
        return context
    except Exception as e:
        print(f'检索上下文失败: {e}')
        return ""
   
   

if __name__ == "__main__":
    asyncio.run(main())