import asyncio
from pathlib import Path

from Agent import Agent
from MCPClient import MCPClient

# Get the current working directory
project_root_dir = Path(__file__).parent.parent

# Example usage of ChatOpenAI
fetch_mcp = MCPClient('fetch', 'uvx', ['mcp-server-fetch']);

# Example usage of MCPClient for file operations
file_mcp = MCPClient('file', 'npx', ["-y","@modelcontextprotocol/server-filesystem",project_root_dir]);

async def main():
    agent = Agent('glm-4.7', [fetch_mcp,file_mcp] ,'你是一个AI助手,请根据用户的问题给出答案')
    await agent.init()
    
    response = await agent.invoke(
        f"爬取https://news.ycombinator.com/的内容，并总结内容保存到{project_root_dir}/output的news.md文件中，然后告诉我文件的大小是多少字节？"
    )
    
    print('Final Response from Agent:')
    print(response)
    await agent.close()
   
   

if __name__ == "__main__":
    asyncio.run(main())